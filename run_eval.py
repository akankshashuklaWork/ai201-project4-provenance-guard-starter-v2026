#!/usr/bin/env python3
"""
Run my five criteria three times each.  <- UNIT 8, MILESTONE 3

    python app.py                              # in one terminal
    python run_eval.py --label before          # in another
    python run_eval.py --label after

The attack set tests what staff thought to test. This tests what *I* thought
to test: the five criteria in criteria.md. `scenarios.py` says what is sent for
each one, and this file sends it, three times, and records what came back.

Three trials, changing nothing in between. Both signals give the same text the
same score every time, so three matching trials are normal and mean the result
holds, not that a step was skipped.

What this file adds to the starter version
    - It counts for me (how many labelled AI, the score spread, how many bad
      requests were refused and logged), so each Run cell in the report has a
      number in it.
    - The appeal criterion needs a submission first and then an appeal on the
      content_id that came back, so there is a "kind" of scenario for that, and
      it reads /log afterwards to check the appeal and the original decision
      are both there.
    - It does NOT decide MET or MISSED. That is a judgement against the target
      in criteria.md, and it is made in the README.
"""

import argparse
import datetime as dt
import json
import sys

import config

# Windows consoles often run a codepage that can't print every character in
# this file's help text. Without this, `--help` ends in a UnicodeEncodeError
# traceback instead of the help.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):  # not a normal text stream
        pass


DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


# ── small helpers ────────────────────────────────────────────────────────────

def safe_json(response):
    """
    The response body as a dict, or {} if it is not JSON.

    A crash in the service makes Flask send back an HTML error page. Without
    this, that would crash the test run too, instead of being recorded.
    """
    try:
        data = response.json()
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def describe(body):
    """A short, readable note of what was sent, for the report."""
    if set(body) == {"text", "creator_id"} and isinstance(body.get("text"), str):
        text = body["text"]
        return text[:70] if text else "(empty text)"
    return json.dumps(body)[:120]


def post_submit(requests, url, body, timeout):
    """
    Send one body to /submit. Returns a result dict, never raises.
    `payload` keeps the full response so callers can look at any field.
    """
    preview = describe(body)
    try:
        response = requests.post(f"{url}/submit", json=body, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - record any failure, keep going
        return {"status": None, "error": f"{type(exc).__name__}: {exc}",
                "sent": preview, "payload": {}}

    payload = safe_json(response)
    return {
        "status": response.status_code,
        "guess": payload.get("guess"),
        "confidence": payload.get("confidence"),
        "model_score": payload.get("model_score"),
        "style_score": payload.get("style_score"),
        "label": payload.get("label"),
        "error": payload.get("error"),
        "sent": preview,
        "payload": payload,
    }


def read_log(requests, url, timeout):
    """Every audit log entry, from GET /log. Empty list if that fails."""
    try:
        return safe_json(requests.get(f"{url}/log", timeout=timeout)).get("entries", [])
    except Exception:  # noqa: BLE001
        return []


def clean(results):
    """Drop the bulky `payload` copy before saving results to the report."""
    return [{k: v for k, v in r.items() if k != "payload"} for r in results]


# ── one function per kind of scenario. Each returns (results, summary) ───────

def run_texts_or_bodies(requests, args, scenario):
    """
    "texts" and "bodies": send each one to /submit and count what came back.
    """
    if scenario.get("kind") == "bodies":
        bodies = list(scenario["bodies"])
    else:
        bodies = [
            {"text": text, "creator_id": f"eval_{scenario['name'][:12]}_{i}"}
            for i, text in enumerate(scenario["texts"], 1)
        ]

    log_before = None
    if scenario.get("check_log"):
        log_before = count_rejected(read_log(requests, args.url, args.timeout))

    results = [post_submit(requests, args.url, body, args.timeout) for body in bodies]
    total = len(results)

    if scenario.get("check_log"):
        # Bad-input criterion: refused cleanly, no 500, and logged.
        refused = sum(1 for r in results
                      if r["status"] in (400, 413) and r.get("error"))
        crashes = sum(1 for r in results if r["status"] is None or r["status"] >= 500)
        logged = count_rejected(read_log(requests, args.url, args.timeout)) - log_before
        summary = f"{refused}/{total} refused cleanly, {crashes} crashes, {logged} logged"
        return results, summary

    # Everything else: how did the labels fall? ("ai" is the high-confidence
    # AI label; "human" and "unsure" are the other two.)
    counts = {"ai": 0, "unsure": 0, "human": 0}
    failed = 0
    for r in results:
        if r["guess"] in counts:
            counts[r["guess"]] += 1
        else:
            failed += 1
    summary = (f"{counts['ai']}/{total} ai, {counts['unsure']} unsure, "
               f"{counts['human']} human")
    if failed:
        summary += f", {failed} not scored"
    return results, summary


def run_spread(requests, args, scenario):
    """
    The spread criterion: average combined score of the AI texts minus the
    average of the human texts.
    """
    results = []
    scores = {"ai": [], "human": []}
    for side in ("ai", "human"):
        for i, text in enumerate(scenario[side], 1):
            body = {"text": text, "creator_id": f"eval_spread_{side}_{i}"}
            result = post_submit(requests, args.url, body, args.timeout)
            result["group"] = side
            results.append(result)
            if isinstance(result.get("confidence"), (int, float)):
                scores[side].append(result["confidence"])

    if not scores["ai"] or not scores["human"]:
        return results, "could not compute (a group got no scores)"

    ai_avg = sum(scores["ai"]) / len(scores["ai"])
    human_avg = sum(scores["human"]) / len(scores["human"])
    summary = f"AI {ai_avg:.3f} - human {human_avg:.3f} = {ai_avg - human_avg:.3f}"
    return results, summary


def run_sweep(requests, args, scenario):
    """
    Part (b) of the label criterion. No web request: walk every score from 0.00
    to 1.00 in steps of 0.01 through scoring.score_to_label and look for a gap
    or an error. This uses the same thresholds the service uses, because both
    read config.py.
    """
    import scoring

    errors = 0
    guesses = {}
    for step in range(0, 101):
        score = step / 100
        try:
            guess, label = scoring.score_to_label(score)
            if guess not in ("human", "unsure", "ai") or not label:
                errors += 1
            guesses[step] = guess
        except Exception:  # noqa: BLE001
            errors += 1

    low, high = guesses.get(51), guesses.get(95)
    summary = (f"{len(guesses)} of 101 scores labelled, {errors} errors, "
               f"labels seen {sorted(set(guesses.values()))}, "
               f"0.51={low} vs 0.95={high}, differ={low != high}")
    results = [{"status": "n/a", "sent": "scores 0.00 to 1.00 in steps of 0.01",
                "errors": errors, "labels_seen": sorted(set(guesses.values())),
                "label_at_0.51": low, "label_at_0.95": high}]
    return results, summary


def count_rejected(entries):
    """How many entries in the log are rejections."""
    return sum(1 for e in entries if e.get("event") == "rejected")


def count_appeals(entries):
    """How many entries in the log are appeals."""
    return sum(1 for e in entries if e.get("event") == "appeal")


def run_appeal(requests, args, scenario, trial):
    """
    The appeal criterion. For each text: submit it, appeal the content_id that
    came back, then read /log and check that
      - the appeal returned 200 with status "under_review",
      - an appeal entry holds my exact reasoning, and
      - the original decision entry is still there and unchanged.
    Finally an appeal on an id that does not exist must return 404 and must not
    write an appeal entry.
    """
    results = []
    submitted = []  # (content_id, reasoning, original response) for each text

    for i, text in enumerate(scenario["texts"], 1):
        body = {"text": text, "creator_id": f"eval_appeal_t{trial}_{i}"}
        sub = post_submit(requests, args.url, body, args.timeout)
        content_id = sub["payload"].get("content_id")
        reasoning = f"Eval trial {trial}, item {i}: I wrote this myself."

        row = {"sent": f"appeal on submission {i}", "content_id": content_id}
        if not content_id:
            row.update({"status": sub["status"], "passed": False,
                        "note": "the submission itself failed"})
            results.append(row)
            continue

        try:
            response = requests.post(f"{args.url}/appeal", timeout=args.timeout,
                                     json={"content_id": content_id, "reasoning": reasoning})
            payload = safe_json(response)
            row.update({"status": response.status_code,
                        "appeal_status": payload.get("status")})
        except Exception as exc:  # noqa: BLE001
            row.update({"status": None, "error": f"{type(exc).__name__}: {exc}"})
        row["_reasoning"] = reasoning
        row["_original"] = sub["payload"]
        results.append(row)

    # Now read the log once and check every appeal against it.
    entries = read_log(requests, args.url, args.timeout)
    passed = 0
    for row in results:
        if "_reasoning" not in row:
            continue
        cid = row["content_id"]
        appeal_logged = any(e.get("content_id") == cid and e.get("event") == "appeal"
                            and e.get("reasoning") == row["_reasoning"] for e in entries)
        decisions = [e for e in entries if e.get("content_id") == cid and "event" not in e]
        original = row["_original"]
        intact = (len(decisions) == 1
                  and decisions[0].get("status") == "decided"
                  and decisions[0].get("guess") == original.get("guess")
                  and decisions[0].get("combined_score") == original.get("confidence"))
        row["appeal_logged"] = appeal_logged
        row["decision_intact"] = intact
        row["passed"] = (row.get("status") == 200 and row.get("appeal_status") == "under_review"
                         and appeal_logged and intact)
        passed += row["passed"]
        del row["_reasoning"], row["_original"]

    # An appeal on an id that does not exist.
    appeals_before = count_appeals(entries)
    try:
        response = requests.post(f"{args.url}/appeal", timeout=args.timeout,
                                 json={"content_id": "doesnotexist00",
                                       "reasoning": "Eval: this id does not exist."})
        unknown_status = response.status_code
    except Exception:  # noqa: BLE001
        unknown_status = None
    appeals_after = count_appeals(read_log(requests, args.url, args.timeout))
    unknown_ok = unknown_status == 404 and appeals_after == appeals_before
    results.append({"sent": "appeal on unknown content_id", "status": unknown_status,
                    "appeal_entry_written": appeals_after != appeals_before,
                    "passed": unknown_ok})

    total = len(scenario["texts"])
    summary = f"{passed}/{total} appeals ok, unknown id -> {unknown_status} (ok={unknown_ok})"
    return results, summary


# ── the main loop ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("The `requests` package isn't installed.\n"
              "Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    try:
        import scenarios
    except ImportError:
        print("No scenarios.py found. Milestone 3 starts by filling it in.",
              file=sys.stderr)
        sys.exit(1)

    problems = scenarios.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except Exception:  # noqa: BLE001
        print(f"Nothing answering at {args.url}. Start it:  python app.py",
              file=sys.stderr)
        sys.exit(1)

    if args.trials < 3:
        print(f"!! {args.trials} trial(s). The submission asks for three.\n")

    rows = []
    for scenario in scenarios.SCENARIOS:
        kind = scenario.get("kind", "texts")
        print(f"\n{scenario['name']}  (criterion {scenario.get('criterion') or '-'})")

        trials, summaries = [], []
        for trial in range(1, args.trials + 1):
            if kind == "spread":
                results, summary = run_spread(requests, args, scenario)
            elif kind == "sweep":
                results, summary = run_sweep(requests, args, scenario)
            elif kind == "appeal":
                results, summary = run_appeal(requests, args, scenario, trial)
            else:
                results, summary = run_texts_or_bodies(requests, args, scenario)

            trials.append(clean(results))
            summaries.append(summary)
            print(f"  trial {trial}: {summary}")

        rows.append({"scenario": scenario, "trials": trials, "summaries": summaries})

    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.trials
    headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' - {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main` (scenarios in `scenarios.py`)",
        "- Service: `app.py::submit` and `app.py::appeal` · scoring: `scoring.py::combine_signals`",
        f"- {n} trials per criterion · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "The Run cells are counted by `run_eval.py`. The Target and Verdict columns",
        "are left blank here: MET or MISSED is a judgement against `criteria.md`,",
        "and it is made in the README.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        name = f"{number}. {scenario['name']}" if number else scenario["name"]
        cells = " | ".join(row["summaries"])
        lines.append(f"| {name} |  | {cells} |  |")

    lines += ["", "---", "", "## What actually came back", "",
              "Real output from each trial, as the service returned it.", ""]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", ""]
        for trial_number, results in enumerate(row["trials"], 1):
            lines += [f"**Trial {trial_number}**", "", "```json",
                      json.dumps(results, indent=2, ensure_ascii=False), "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path.relative_to(config.ROOT)}")
    print("Commit it. It's the evidence the test actually happened.")


if __name__ == "__main__":
    main()
