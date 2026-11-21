#!/usr/bin/env python3
"""
Provenance Guard — the web service.

    python app.py

Then, in another terminal:

    curl -X POST http://127.0.0.1:5000/ping \
      -H "Content-Type: application/json" \
      -d '{"message": "hello"}'

That's the example route. It works right now, before you've written anything.
**Leave it alone** — it's your control. When something breaks later, check that
`/ping` still answers: if it does, the problem is in your handler; if it
doesn't, it's the service itself.

Routes:

    POST /ping        the worked example. Already works. Don't edit it
    POST /submit      ← YOU BUILD THIS (Milestone 3, 4, 5)
    POST /appeal      ← YOU BUILD THIS (Milestone 5)
    GET  /log         the audit log. Already works
    GET  /health      is the service up, and is the model loaded
"""

import uuid

from flask import Flask, jsonify, request

import audit
import config
import detector
import scoring
import stylometry

app = Flask(__name__)


# ── Rate limiting — UNIT 8 ────────────────────────────────────────────────────
# Off until you turn it on. In unit 8, Milestone 1:
#
#   1. Set RATE_LIMITING_ENABLED = True in config.py (or AI201_RATE_LIMITS=1)
#   2. Choose your numbers there
#   3. Uncomment the @limiter.limit(...) line on /submit below
#
# The order doesn't matter. While limiting is off, that decorator is a no-op
# that quietly does nothing, so uncommenting it early costs you nothing — but
# it also means no 429 until you've done step 1.
#
# The storage backend is preconfigured, which stops Flask-Limiter printing a
# warning on every start. In-memory is right for one laptop and wrong for
# anything real — a restart forgets every count.

class _LimiterOff:
    """
    Stands in for the real limiter while rate limiting is off.

    It makes @limiter.limit(...) a decorator that returns the route
    untouched, so uncommenting the line before you flip the setting is
    harmless instead of a crash on startup.
    """

    def limit(self, *args, **kwargs):
        return lambda view: view


limiter = _LimiterOff()
if config.RATE_LIMITING_ENABLED:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def rate_limit_key():
        """
        Who a request counts against.

        Falling back to the caller's address is the easy version. Unit 8's
        stretch asks about per-creator limits instead — and the difference
        matters: one script can look like a thousand callers, and one household
        can look like one.
        """
        payload = request.get_json(silent=True)
        # A body that parses as JSON but isn't an object — a bare list or
        # string — has no .get. Without this guard the key function raises
        # BEFORE the route runs, and a malformed request becomes a 500 that
        # looks like your handler crashed when your handler never ran.
        if not isinstance(payload, dict):
            return get_remote_address()
        creator = payload.get("creator_id")
        return creator if isinstance(creator, str) and creator.strip() else get_remote_address()

    limiter = Limiter(
        key_func=rate_limit_key,
        app=app,
        storage_uri=config.RATE_LIMIT_STORAGE,
        default_limits=[],
    )

    @app.errorhandler(429)
    def rate_limited(exc):
        """
        A rejected request still leaves a trace.

        ⚠️ An attack that shows up only as an absence is one you'll never find.
        """
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            payload = {}
        audit.log_rejection(
            creator_id=payload.get("creator_id", "unknown"),
            reason="rate_limited",
            limit=str(exc.description),
        )
        return jsonify({
            "error": "rate_limited",
            "message": "Too many submissions. Try again shortly.",
            "limit": str(exc.description),
        }), 429


# ── The worked example. Already works. Don't edit. ────────────────────────────

@app.post("/ping")
def ping():
    """
    Everything a route needs, in six lines.

    JSON arrives as a dict. You pull things out of it. You return a dict and
    the framework turns it into a response. That's the whole idea.
    """
    payload = request.get_json(silent=True) or {}
    return jsonify({
        "ok": True,
        "you_sent": payload.get("message"),
        "service": "provenance-guard",
    })


@app.get("/health")
def health():
    """Is the service up, and has the model been downloaded yet?"""
    import detector

    loaded = detector._model is not None
    return jsonify({
        "ok": True,
        "detector_model": config.DETECTOR_MODEL,
        "detector_loaded": loaded,
        "rate_limiting": config.RATE_LIMITING_ENABLED,
        "log_entries": len(audit.read_entries()),
    })


# ── YOU BUILD THIS ────────────────────────────────────────────────────────────

@app.post("/submit")
# @limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute;{config.RATE_LIMIT_PER_DAY}/day")
def submit():
    """
    Take a piece of text, decide about it, log the decision, answer.

    Expects JSON:
        {"text": "...", "creator_id": "..."}

    Returns JSON:
        {"content_id": "...", "guess": "...", "confidence": 0.0, "label": "...",
         "model_score": 0.0, "style_score": 0.0}

    `confidence` is the combined score on a 0-1 line: 0.0 means "confidently a
    person wrote this", 1.0 means "confidently a machine did", and the middle
    means the system genuinely isn't sure.

    The steps, in order:
        1. Check the request is usable (400 / 413 if not, and log the refusal)
        2. Run signal one (the model) and signal two (the text's shape)
        3. Combine them into one score
        4. Turn the score into a guess and a label a person can read
        5. Write everything to the audit log, then answer
    """
    payload = request.get_json(silent=True)

    # ── Step 1: refuse bad input politely. Never let it crash into a 500. ──
    # A body that isn't a JSON object at all (a bare list, a string, nothing)
    # has no .get(), so we turn it into an empty dict first.
    if not isinstance(payload, dict):
        payload = {}

    text = payload.get("text")
    creator_id = payload.get("creator_id")

    problem = _check_input(text, creator_id)
    if problem:
        reason, message, status_code = problem
        # `creator_id` may be missing or the wrong type, so only log it if it
        # is a string. "unknown" is clearer than writing a number or null.
        who = creator_id if isinstance(creator_id, str) and creator_id.strip() else "unknown"
        audit.log_rejection(creator_id=who, reason=reason)
        return jsonify({"error": reason, "message": message}), status_code

    text = text.strip()

    # ── Step 2: both signals. ──
    try:
        model_score = detector.model_signal(text)
    except detector.DetectorUnavailable as exc:
        # The model couldn't load (not downloaded, no disk). That is the
        # service's problem, not the writer's, so it's a 503.
        audit.log_rejection(creator_id=creator_id, reason="detector_unavailable")
        return jsonify({"error": "detector_unavailable", "message": str(exc)}), 503
    except ValueError as exc:
        # The detector refuses text that is only a token or two.
        audit.log_rejection(creator_id=creator_id, reason="text_too_short")
        return jsonify({"error": "text_too_short", "message": str(exc)}), 400

    style_score = stylometry.style_signal(text)

    # ── Step 3: one number out of two. ──
    combined_score = round(scoring.combine_signals(model_score, style_score), 4)

    # ── Step 4: the number becomes a guess and a plain-English label. ──
    guess, label = scoring.score_to_label(combined_score)

    # ── Step 5: log it, then answer. The content_id is how /appeal finds it. ──
    content_id = uuid.uuid4().hex[:12]

    audit.log_decision(
        content_id=content_id,
        creator_id=creator_id,
        guess=guess,
        model_score=model_score,
        style_score=style_score,
        combined_score=combined_score,
        label=label,
        status="decided",
    )

    return jsonify({
        "content_id": content_id,
        "guess": guess,
        "confidence": combined_score,
        "label": label,
        "model_score": model_score,
        "style_score": style_score,
        "status": "decided",
    })


def _check_input(text, creator_id):
    """
    Decide whether a /submit request is usable.

    Returns None if it is fine, or (reason, message, http_status) if not.
    Kept as its own small function so the rules are easy to read in one place.
    """
    # creator_id must be a non-empty string
    if not isinstance(creator_id, str) or not creator_id.strip():
        return ("missing_creator_id",
                "Please include a creator_id (a non-empty string).", 400)

    # text must exist and be a string
    if text is None:
        return ("missing_text", "Please include the text to check.", 400)
    if not isinstance(text, str):
        return ("text_not_a_string", "text must be a string.", 400)

    # text must have something in it besides spaces
    if not text.strip():
        return ("empty_text", "The text is empty.", 400)

    # text must not be enormous
    if len(text) > config.MAX_TEXT_CHARS:
        return ("text_too_long",
                f"The text is over {config.MAX_TEXT_CHARS:,} characters. "
                f"Please submit a shorter piece.", 413)

    return None


@app.post("/appeal")
def appeal():
    """
    A writer says we got it wrong.

    Expects JSON:
        {"content_id": "...", "reasoning": "..."}

    What it does:
      1. Checks the request is usable (400 if not).
      2. Checks the content_id really exists in the log (404 if not). A typo
         here would otherwise fail silently and look like a broken endpoint.
      3. Records the appeal with audit.log_appeal(), which sets the status to
         "under_review". The log is append-only, so the original decision stays
         exactly as it was and the appeal sits after it.
      4. Confirms to the writer. Nothing is re-checked automatically.

    This is the smallest endpoint in the project and the one that matters most
    to the person on the other end: it is the only thing standing between a
    wrong accusation and nothing at all.
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}

    content_id = payload.get("content_id")
    reasoning = payload.get("reasoning")

    # ── Step 1: is the request usable? ──
    if not isinstance(content_id, str) or not content_id.strip():
        audit.log_rejection(creator_id="unknown", reason="appeal_missing_content_id")
        return jsonify({
            "error": "missing_content_id",
            "message": "Please include the content_id you were given.",
        }), 400

    if not isinstance(reasoning, str) or not reasoning.strip():
        audit.log_rejection(creator_id="unknown", reason="appeal_missing_reasoning",
                            content_id=content_id)
        return jsonify({
            "error": "missing_reasoning",
            "message": "Please tell us why you think this was wrong.",
        }), 400

    if len(reasoning) > config.MAX_REASONING_CHARS:
        audit.log_rejection(creator_id="unknown", reason="appeal_reasoning_too_long",
                            content_id=content_id)
        return jsonify({
            "error": "reasoning_too_long",
            "message": f"Please keep your explanation under "
                       f"{config.MAX_REASONING_CHARS:,} characters.",
        }), 413

    # ── Step 2: does this content_id exist? ──
    # An item exists if the log holds a decision for it (a decision entry has
    # no "event" field; appeals and rejections do).
    history = audit.entries_for(content_id.strip())
    decisions = [entry for entry in history if "event" not in entry]
    if not decisions:
        audit.log_rejection(creator_id="unknown", reason="appeal_unknown_content_id",
                            content_id=content_id)
        return jsonify({
            "error": "unknown_content_id",
            "message": "We couldn't find a submission with that content_id. "
                       "Please check it and try again.",
        }), 404

    # ── Step 3: record it next to the original decision. ──
    original = decisions[0]
    audit.log_appeal(
        content_id=content_id.strip(),
        creator_id=original.get("creator_id", "unknown"),
        reasoning=reasoning.strip(),
    )

    # ── Step 4: confirm. ──
    return jsonify({
        "content_id": content_id.strip(),
        "status": "under_review",
        "message": "Thank you. Your appeal has been recorded and this piece is "
                   "now under review. We have not changed anything about your "
                   "work in the meantime.",
    })


# ── Already works ─────────────────────────────────────────────────────────────

@app.get("/log")
def get_log():
    """
    The audit log, most recent last.

        curl "http://127.0.0.1:5000/log?limit=10"

    You need this in unit 8 to paste entries into your README, and you need it
    now to see whether your logging is actually working.
    """
    limit = request.args.get("limit", type=int)
    entries = audit.read_entries(limit=limit)
    return jsonify({"count": len(entries), "entries": entries})


def main():
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}")
    print(f"  detector model:  {config.DETECTOR_MODEL}")
    print(f"  rate limiting:   {'ON' if config.RATE_LIMITING_ENABLED else 'off (unit 8)'}")
    print(f"  audit log:       {config.AUDIT_LOG}")
    print()
    print("Check it's alive:")
    print(f'  curl -X POST http://{config.HOST}:{config.PORT}/ping \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"message\": \"hello\"}'")
    print()
    # debug=True hands out an interactive debugger, so it's local-only — see config.py
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == "__main__":
    main()
