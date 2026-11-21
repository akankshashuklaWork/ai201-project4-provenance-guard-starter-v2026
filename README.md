# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

Provenance Guard is a small web service a writing site could plug into. Text goes
in; a guess, a score, a plain-English label and a way to appeal come out. Nothing
calls an outside service: the model runs on the laptop.

**The path one submission takes** (this is the Milestone 1 trace):

1. **Arrives at `POST /submit`** (`app.py::submit`) as JSON: `{"text", "creator_id"}`.
2. **Input check** (`app.py::_check_input`). Missing, empty, non-string or enormous
   text, or a missing `creator_id`, is refused with a 400 (413 if over 20,000
   characters). The refusal is written to the log as a `rejected` entry. It never
   becomes a 500.
3. **Signal one** (`detector.py::model_signal`) runs gpt2 locally and measures how
   predictable the text is. Adds `model_score`, 0 to 1, higher = more AI-like.
4. **Signal two** (`stylometry.py::style_signal`) measures the shape of the text:
   sentence-length spread, punctuation, word variety. Adds `style_score`, same
   direction.
5. **Combine** (`scoring.py::combine_signals`) turns the two into one `confidence`
   score, 0 (confidently human) to 1 (confidently AI).
6. **Label** (`scoring.py::score_to_label`) maps the score to one of three guesses
   (`human`, `unsure`, `ai`) and the sentence a reader sees.
7. **Log and answer** (`audit.py::log_decision`). One line is appended to
   `logs/audit.jsonl` holding the content_id, creator, guess, **both signal scores,
   the combined score**, label and status `decided`. The same fields go back to the
   caller.

**The false positive, followed through.** A real writer submits plain, honest
work, for example someone writing in a second language in short simple sentences.
Signal one finds that text very predictable (0.80), because predictable is what
plain writing is. Signal two sees ordinary sentences and few commas, so it leans
human (0.53). The combined score lands near 0.67 and the label can say "this looks
a lot like AI" about work they wrote themselves (this really happened, see Sample
Run). Their way out is `POST /appeal` with their `content_id` and their reasoning.
That sets the item to `under_review` and records what they said next to the
original decision. Everything about thresholds exists to make that situation
rarer; the appeal exists for when it happens anyway.

**The two endpoint shapes**

| | `POST /submit` | `POST /appeal` |
|---|---|---|
| In | `{"text": string, "creator_id": string}` | `{"content_id": string, "reasoning": string}` |
| Out (200) | `content_id`, `guess` (`ai`/`human`/`unsure`), `confidence` (0 to 1), `label` (sentence), `model_score`, `style_score`, `status` (`decided`) | `content_id`, `status` (`under_review`), `message` |
| Out (error) | `{"error": code, "message": text}` with 400, 413 or 503 | same shape with 400, 404 or 413 |

`confidence` is the combined score on the human-to-AI line, so 0.51 and 0.95 are
different answers, not the same answer at different volumes.

**A note on the test texts.** The paragraphs I used to calibrate
(`calibration_texts.py`, scored by `calibration_run.py`) were drafted for testing:
they are not collected from real people, and they are not my own writing. They are
a fair first check, not proof. Replace the plain-human ones with real paragraphs
before trusting criterion 1.

---

## Signals and Scoring

### Signal one — the model signal

**What it measures:** How predictable the text is to a small language model (gpt2,
running locally). Predictability is measured as perplexity, then squashed onto 0 to
1 in `detector.py::model_signal` (midpoint 45, steepness 1.6, left as the starter
set them).

**Why that might differ between human and AI writing:** A language model writes by
repeatedly choosing a likely next word, so its output tends to be text another model
finds easy to predict. Human writing wanders more: odd word choices, abrupt turns,
specific details.

**What it can't see:** Who wrote it. It sees predictability, and plain human writing
is predictable too. On my calibration set the plain human paragraphs scored 0.68 to
0.86, the same as clearly-AI text (0.79 to 0.96). It also reads dense or ornate
human prose as human just because the words are rare, so AI text padded with unusual
words would slip past it. The people it is most likely to wrongly accuse (new writers,
second-language writers, anyone writing plainly) are the ones with the least room to
argue.

### Signal two — the style signal

**What it measures:** The text as text, without understanding it
(`stylometry.py`), three measures, each stretched onto 0 to 1 where 1 means AI-like:

| Measure | What it counts | Direction | Weight |
|---|---|---|---|
| `sentence_length_spread` | stdev of sentence length divided by mean | low spread = AI-like (flipped) | 0.50 |
| `punctuation_density` | commas, semicolons, colons, dashes, brackets, `?` and `!` per word | more = AI-like (not flipped) | 0.35 |
| `type_token_ratio` | unique words over total words, first 100 words only | low = AI-like (flipped) | 0.15 |

**Why that might differ between human and AI writing:** Generated prose tends to
have even, mid-length sentences and a comma-heavy rhythm ("Furthermore, ...",
"Additionally, ..."). Human writing is lumpier: a three-word sentence next to a
forty-word one.

**What it can't see:** Meaning. Anything that changes the shape without changing the
substance moves it: adding typos, splitting or joining sentences, dropping in a short
aside. My lightly-edited AI sample, with typos and one short added sentence, moved from
0.63 to 0.68 (the unedited versions) down to 0.36 and 0.53 on this signal. Plain human writing also looks "even", so it only
helps because it has few commas. Formal human writing is comma-heavy, so it leans
AI-like here (0.65 to 0.66 on my two formal samples). The weakest part is
`type_token_ratio`: on short texts it did not separate human from AI at all, so I gave
it the smallest weight, and typos would inflate it.

### The combining rule

**The rule:** Take the weighted average of the two signals, then apply a
*disagreement guard*: if the signals are more than 0.30 apart, the result may not go
above 0.60, which is below the AI threshold. A split decision therefore can never
produce a high-confidence AI label by itself. The guard only lowers scores, so it only
makes the system more careful about accusing someone.

**The numbers** (all in `config.py`):

- `WEIGHT_MODEL_SIGNAL = 0.5`, `WEIGHT_STYLE_SIGNAL = 0.5`
- `DISAGREEMENT_GAP = 0.30`, `DISAGREEMENT_CAP = 0.60`
- Thresholds: `HUMAN_THRESHOLD = 0.40`, `AI_THRESHOLD = 0.65`

**Where it lives:** `scoring.py::combine_signals`

**A case where my two signals split, and what my rule does with it:** Plain human
paragraph 4 in my calibration set ("My brother and I like to cook on Sundays ...")
scored 0.856 on the model signal and only 0.511 on the style signal. A plain average
gives 0.68, which is a high-confidence AI label on a real person's writing. The gap
is 0.345, more than 0.30, so the guard caps it at 0.60 and it comes out "unsure".
Reason for choosing a cap over a different weighting: two methods disagreeing really is
uncertainty, and on a writing site the wrong accusation costs more than a missed
detection.

**What I tuned, and what that means.** I looked at my 24 calibration texts before
setting the style anchors and moved `HUMAN_THRESHOLD` from the starter's 0.35 to 0.40
(two of five casual human pieces sat at 0.42 and were stuck in "unsure"). So the
results on that set are flattering. Proof: a *new* plain-human paragraph drafted
afterwards (the Sample Run below) was labelled high-confidence AI. Where I expect this
to fail is next unit's job to find.

**What the numbers looked like** (`python calibration_run.py`, average combined score):
clearly-AI 0.82, casual human 0.36, plain human 0.56, formal human 0.56, lightly-edited
AI 0.50. Clearly-AI minus casual human is 0.46, but clearly-AI minus plain human is
only 0.26, short of my criterion-2 target of 0.30 if plain writing is counted as the
"human" side. Lightly-edited AI lands in "unsure", so it gets through, which is the
price of caring more about false accusations.

---

## Label Variants

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 to under 0.40 | "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do." |
| unsure | 0.40 to 0.65 (both edges included) | "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review." |
| high-confidence AI | over 0.65 to 1.00 | "This looks a lot like writing produced by an AI tool. Our check can be wrong, and if you wrote this yourself we would like to hear from you. You can ask for a review and a person will look at it." |

All three are reachable: my calibration run produces each one, and `scoring.label_ranges()`
prints the same ranges with no gap. A score of 0.51 gives "unsure" and 0.95 gives "AI".

**Why I worded the "unsure" one this way:** The person reading it may well have written
every word themselves, so it says plainly that no judgement has been made, tells them
not to read anything into it, and points to a way to ask a person to look. It never says
"suspicious" or "flagged", and it names plain, simple writing as a known blind spot so a
writer who writes that way is told it is not about them. I have not yet tested it on
another reader, so whether it comes across as reassuring or as confusing is open.

---

## Sample Run

This is a real run against the running service. The paragraph is a plain human
paragraph written for this test (not part of the calibration set), and it shows the
false-positive case from the trace: a real writer gets the AI label, then appeals.

**A submission**

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "I walked to the library after school today. It was raining so I took my umbrella. I found the book I wanted on the second shelf. The librarian was kind and helped me check it out. Then I walked home and started reading.", "creator_id": "writer_sample_1"}'
```

```json
{
  "confidence": 0.6663,
  "content_id": "5c48b7f2f31b",
  "guess": "ai",
  "label": "This looks a lot like writing produced by an AI tool. Our check can be wrong, and if you wrote this yourself we would like to hear from you. You can ask for a review and a person will look at it.",
  "model_score": 0.8005,
  "status": "decided",
  "style_score": 0.5322
}
```

**An appeal** (on that content_id)

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "5c48b7f2f31b", "reasoning": "I wrote this myself. I always write in short, simple sentences because English is my second language."}'
```

```json
{
  "content_id": "5c48b7f2f31b",
  "message": "Thank you. Your appeal has been recorded and this piece is now under review. We have not changed anything about your work in the meantime.",
  "status": "under_review"
}
```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=2"
```

```json
{
  "count": 2,
  "entries": [
    {
      "combined_score": 0.6663,
      "content_id": "5c48b7f2f31b",
      "creator_id": "writer_sample_1",
      "guess": "ai",
      "label": "This looks a lot like writing produced by an AI tool. Our check can be wrong, and if you wrote this yourself we would like to hear from you. You can ask for a review and a person will look at it.",
      "model_score": 0.8005,
      "status": "decided",
      "style_score": 0.5322,
      "timestamp": "2026-11-21T08:12:52+00:00"
    },
    {
      "content_id": "5c48b7f2f31b",
      "creator_id": "writer_sample_1",
      "event": "appeal",
      "reasoning": "I wrote this myself. I always write in short, simple sentences because English is my second language.",
      "status": "under_review",
      "timestamp": "2026-11-21T08:12:52+00:00"
    }
  ]
}
```

The original decision is still there, unchanged, and the appeal sits after it with the
status `under_review`. `logs/audit.jsonl` is committed and also holds the full
calibration run, five more appeals and the refused bad inputs.

**A pre-check of my criteria (one pass, not the three-trial run, which is next unit).**
Against the live service: 0 of 10 plain human pieces labelled AI (but see the tuning
note above); 6 of 6 bad inputs handled with a 400 or 413, none a 500, all logged; all
three labels seen; 5 of 5 appeals returned `under_review` with the original decision
intact and an unknown id gave a 404. Criterion 2 is the one I expect to miss: 0.46
against casual human writing, 0.26 against plain human writing.

---

## How I Used AI

I used an AI assistant for this whole unit: I gave it the assignment and asked it to
complete it. That is a lot of AI, so here are the two moments that mattered most and
exactly what was mine and what was not.

**Moment 1: the acceptance criteria**

- *What I asked for:* Criteria for a system where being wrong has a cost. The
  assistant would not choose the standard for me, so it asked me four multiple-choice
  questions: how many human pieces in 10 may be called AI, how far apart AI and human
  text must score, what happens on bad input, and which other areas to cover.
- *What came back:* Five criteria written out in full with a reason under each, after I
  had answered. It offered 1 in 10, 0 in 10 or 2 in 10 as the false-positive target.
- *What I changed:* The numbers are my choices, not the assistant's: I picked the
  loosest false-positive option (at most 2 in 10) and a spread of 0.30. The assistant
  wrote the wording and the "why" paragraphs from those choices, and I disclose that at
  the top of `criteria.md`. The criteria were committed before any code, so no result
  could shape them. I should be honest that 2 in 10 is a higher rate than I'd want for a
  real site.

**Moment 2: the combining rule**

- *What I asked for:* A way to turn two scores into one that respects the
  false-positive concern from the brief.
- *What came back:* A first weighted average that, on my calibration table, would have
  labelled a plain human paragraph "high-confidence AI" (0.68) because the model signal
  was sure (0.86) while the style signal was not (0.51). The assistant proposed the
  disagreement guard to deal with exactly that case.
- *What I changed:* Nothing in the guard's logic; the weights, the 0.30 gap, the 0.60 cap
  and the thresholds are the assistant's numbers, set from the table. I also moved
  `HUMAN_THRESHOLD` from 0.35 to 0.40 after seeing the table. Both choices were made
  looking at my own test texts, which is why I do not trust the results on them, and why
  the final test paragraph, which the guard did *not* save, is in the Sample Run above.
- *Update from unit 8:* The attack set showed the guard did less than I thought. Across all
  56 attacks it changed a label in only three (EV10, MF06 and MF07, each from "ai" to
  "unsure") and it saved none of the eight false-positive attacks, because their plain
  averages were already at or under 0.60. It let one real AI attack through (EV10). I built
  it from a single calibration paragraph, which was not enough evidence.

**Unit 8, Milestone 1: the rate limit numbers**

- *What I asked for:* Turn on rate limiting and the audit log for the test unit.
- *What came back:* The assistant switched the limiter on, chose 5 a minute and 100 a
  day, wrote the reasons under Rate Limiting, and ran the 15-request flood test.
- *What I changed:* Nothing yet. These two numbers are the assistant's proposal and I
  have to decide whether I agree with the reasoning before I submit.

**Unit 8, Milestones 2 and 3: the attack run, my own writing and the verdicts**

- *What I asked for:* Run the attack set and my five criteria, and write up the results.
- *What came back:* The assistant ran both, marked each attack held or broke, extended
  `run_eval.py` (it now counts results and tests the appeal path), wrote `scenarios.py`,
  and drafted the verdicts and diagnoses. While checking its own draft it found that its
  first claim about the disagreement guard was wrong (the guard saved no false positives),
  and corrected it in the README.
- *What I changed:* The held-or-broke marks and diagnoses are the assistant's draft and
  still need my review. My "own writing" for criterion 1 is real: with my permission the
  assistant read some of my sent email and copied ten short lines word for word. It left out
  two emails that looked pasted from an AI tool, and anything about immigration, health or
  ID numbers. I still need to confirm I wrote piece 2 myself.

**Unit 8, Milestones 5 and 6: the improvement and what is still broken**

- *What I asked for:* Choose one improvement from my diagnosis, make it, run everything
  again, and write up what is still broken.
- *What came back:* The assistant recommended input validation and I picked it over
  reweighting the style signal. It added the 12-word minimum (`app.py::_check_input`,
  `config.py::MIN_WORDS`), ran the attack set and my five criteria again, checked in code
  that no other attack's score changed, and drafted The Improvement, What's Still Broken and
  the production trade. The 12-word number and the wording are the assistant's.
- *What I changed:* *(draft, to be replaced with what I actually change)* I chose the type of
  improvement. I still have to read the write-up and decide whether I agree that the cost of
  refusing short writing is worth it, and whether I would make the same production trade.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 100 per day, on `POST /submit` only
(`config.py::RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_PER_DAY`, applied by the
`@limiter.limit(...)` line above `app.py::submit`).

**Why those numbers and not others:**

- *A real writer.* Checking a piece takes a second or two, and nobody writes five
  new pieces inside one minute. 5 a minute leaves room for someone pasting a few
  drafts in a row, or retrying after a typo. 100 a day is far more than anyone checks
  by hand, so a normal writer never meets either limit.
- *A script mapping my thresholds.* Without a limit, a script can send roughly 30
  submissions a minute (each takes 1-2 seconds), so a thousand variations take well
  under an hour. 5 a minute slows that to one every 12 seconds, and the daily cap
  stops it at 100 probes. That is not enough to trace where the 0.40 and 0.65 lines
  sit by trial and error from a single creator_id.
- *Why not lower.* 1 or 2 a minute would start refusing honest writers, and a refused
  writer gets no answer at all, which is worse than a wrong one. *Why not higher.* At
  10 a minute and 200 a day (the starter's defaults) a script gets twice as many probes
  for no benefit to writers.
- These are my judgement, not measured from real traffic, because there is none.

**What a caller counts as:** the `creator_id` in the request body, falling back to the
caller's address when there is no usable `creator_id`
(`app.py::rate_limit_key`). I kept this per-creator rather than per-address on purpose:
the attack set sends everything from one machine under different creator_ids, so an
address limit would block the whole run. The weakness is the one the brief warns
about: `creator_id` is something the caller types, so a script can get around this
limit by changing it on every request. The limit stops one account hammering the
service; it does **not** stop a determined attacker. Fixing that needs real accounts
(a creator_id the service issues, not one the caller supplies). Counts are kept in
memory, so restarting the service forgets them.

**The run of status codes when I pushed past it** (`python run_attacks.py --flood 15`,
saved in `results/flood_2026-11-21_0028.md`):

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

The first five went through and the next ten were refused. All ten refusals are in the
audit log, for example:

```json
{"creator_id": "flood_tester", "event": "rejected", "limit": "5 per 1 minute", "reason": "rate_limited", "status": "rejected", "timestamp": "2026-11-21T08:28:32+00:00"}
```

`GET /health` now answers `"rate_limiting": true`.

---

## Attack Run — Before

Run with `python run_attacks.py --set attack_set --label before` against the service
with rate limiting on (5 a minute, 100 a day). Full output:
`results/attack_run_2026-11-21_0034_before.md`. All 56 attacks got a recorded outcome and
**no attack crashed the service** (0 responses of 5xx).

**Score: 42 held, 14 broke, out of 56.** (The marks are mine to defend; the run
script marks nothing but crashes.)

**How I marked them.** An *evasion* attack (AI text trying to get past) is HELD only if the
label was "high-confidence AI"; "unsure" and "human" both mean it got past, so both are BROKE. An
*injection* attack is BROKE if the instruction got the result it asked for (PI01 and PI02 asked to
be cleared as human, PI04 asked for a hostile label, PI05 for a forged log line) and HELD if not
(PI03 and PI06 stayed "unsure"). A *false-positive* attack (human text) is BROKE only if the writer
was labelled AI; "unsure" is HELD because nobody was accused. A *malformed* request is HELD if it was
refused cleanly or, for odd text that was accepted, if the answer was honestly "unsure"; it is BROKE
if junk was accepted and labelled "human". A request that is refused (400) counts as HELD even if the
attack was a short AI text: it did not get through, though it was not detected either. Flood rows are
HELD if the limit stopped them and logged it.

| Family | Held | Broke |
|---|---|---|
| evasion (10) | 1 | 9 (2 labelled human, 7 stuck at unsure) |
| false_positive (8) | 7 | 1 |
| prompt_injection (6) | 4 | 2 |
| malformed (20) | 18 | 2 |
| flood_same_creator (12) | 12 | 0 |

| ID | Family | What it went for | Status | Guess | Score | Mark | Why |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | unsure | 0.436 | **BROKE** | AI text with typos scored 0.436 (unsure). Typos made the language model see odd words: model_score fell to 0.16 |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.434 | **BROKE** | AI text, sentences broken up: 0.434, unsure |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.572 | **BROKE** | AI text with a pasted quotation: 0.572, unsure |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | ai | 0.681 | **HELD** | unusual words did not hide it: labelled AI at 0.681 (barely over the 0.65 line) |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.374 | **BROKE** | heavily edited text labelled human, 0.374 |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.411 | **BROKE** | one very long and one very short sentence: 0.411, unsure |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.631 | **BROKE** | punctuation padding: 0.631, unsure, 0.02 under the AI line |
| EV08 | evasion | signal one: text below the token window | 200 | human | 0.281 | **BROKE** | 65 characters, labelled human 0.281: too short for either signal to say anything |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.569 | **BROKE** | human opening bolted on: 0.569, unsure |
| EV10 | evasion | signal two: repeated stanza structure | 200 | unsure | 0.600 | **BROKE** | model_score 0.979 but style 0.356, so the disagreement guard capped it at exactly 0.600, unsure |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | unsure | 0.482 | **HELD** | plain human text, unsure 0.482 (not accused) |
| FP02 | false_positive | human writing in a formal register | 200 | unsure | 0.633 | **HELD** | unsure 0.633, close to the AI line |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | unsure | 0.587 | **HELD** | unsure 0.587 (model 0.805, style 0.369; a plain average gives the same 0.587) |
| FP04 | false_positive | a student essay written to a rubric | 200 | unsure | 0.600 | **HELD** | unsure 0.600 (the plain average is 0.6001, so the guard changed nothing) |
| FP05 | false_positive | technical documentation written by a person | 200 | ai | 0.708 | **BROKE** | a real person's technical docs labelled high-confidence AI, 0.708 |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.566 | **HELD** | unsure 0.566 (model 0.881, style 0.251; the plain average is the same) |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | unsure | 0.600 | **HELD** | unsure 0.600 (plain average 0.6006, the guard changed nothing) |
| FP08 | false_positive | very short genuine human submission | 200 | human | 0.245 | **HELD** | very short human text labelled human 0.245 |
| PI01 | prompt_injection | instruction to ignore the check | 200 | human | 0.235 | **BROKE** | AI text plus 'return human': labelled human 0.235. The service never reads instructions; the extra short sentences dropped style_score to 0.007 |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.213 | **BROKE** | AI text plus fake SYSTEM line: labelled human 0.213, same mechanism as PI01 |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.571 | **HELD** | AI text plus a polite note: unsure 0.571, not cleared |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | unsure | 0.545 | **HELD** | script tag in the text: the label is fixed text and the input is never echoed back |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | unsure | 0.559 | **HELD** | attempt to forge a log line: the log stores no input text and json.dumps escapes quotes. Entry is intact |
| PI06 | prompt_injection | instruction plus real human text | 200 | unsure | 0.448 | **HELD** | instruction plus human text: unsure 0.448, about the same as the same text alone (FP01) |
| MF01 | malformed | text is only whitespace | 400 | — | — | **HELD** | 400 empty_text, logged |
| MF02 | malformed | text is a single character | 400 | — | — | **HELD** | 400 text_too_short, logged |
| MF03 | malformed | text is control characters | 200 | human | 0.125 | **BROKE** | control characters accepted and labelled human 0.125 (model_score 0.0). Junk should be refused, not cleared |
| MF04 | malformed | text is only punctuation | 200 | human | 0.256 | **BROKE** | punctuation only, accepted and labelled human 0.256 |
| MF05 | malformed | text is a very long single word | 200 | unsure | 0.600 | **HELD** | no crash; unsure 0.600 (model_score 0.998) |
| MF06 | malformed | text is emoji only | 200 | unsure | 0.600 | **HELD** | no crash; unsure 0.600 (the guard lowered it from 0.748, which would have been AI) |
| MF07 | malformed | text is right-to-left script | 200 | unsure | 0.600 | **HELD** | no crash; unsure 0.600 (the guard lowered it from 0.703, which would have been AI) |
| MF08 | malformed | text is 60,000 characters | 413 | — | — | **HELD** | 413 text_too_long, logged |
| RQ01 | malformed | no text field at all | 400 | — | — | **HELD** | 400 missing_text, logged |
| RQ02 | malformed | no creator_id | 400 | — | — | **HELD** | 400 missing_creator_id, logged |
| RQ03 | malformed | text is a number | 400 | — | — | **HELD** | 400 text_not_a_string, logged |
| RQ04 | malformed | text is a list | 400 | — | — | **HELD** | 400 text_not_a_string, logged |
| RQ05 | malformed | text is null | 400 | — | — | **HELD** | 400 missing_text, logged |
| RQ06 | malformed | creator_id is an object | 400 | — | — | **HELD** | 400 missing_creator_id, logged |
| RQ07 | malformed | body is a JSON array, not an object | 400 | — | — | **HELD** | 400, logged |
| RQ08 | malformed | body is unparseable JSON | 400 | — | — | **HELD** | 400, logged |
| RQ09 | malformed | body is empty | 400 | — | — | **HELD** | 400, logged |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | — | — | **HELD** | first pass came back 429 (see note below); re-run alone it returns 400 missing_creator_id |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | — | — | **HELD** | first pass came back 429 (see note below); re-run alone it returns 400 missing_creator_id |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | **HELD** | 400 text_not_a_string, logged |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | human | 0.139 | **HELD** | accepted: inside the 5-a-minute limit |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | human | 0.139 | **HELD** | accepted: inside the 5-a-minute limit |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | human | 0.139 | **HELD** | accepted: inside the 5-a-minute limit |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | human | 0.139 | **HELD** | accepted: inside the 5-a-minute limit |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | human | 0.139 | **HELD** | accepted: inside the 5-a-minute limit |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | **HELD** | 429 rate_limited, logged |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | **HELD** | 429 rate_limited, logged |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | **HELD** | 429 rate_limited, logged |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | **HELD** | 429 rate_limited, logged |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | **HELD** | 429 rate_limited, logged |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | **HELD** | 429 rate_limited, logged |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | **HELD** | 429 rate_limited, logged |

**A note on RQ10 and RQ11.** On the first pass both returned 429. They were not
refused by my route: my own limiter stopped them first. Those two requests, like RQ02,
RQ06, RQ07, RQ08 and RQ09 before them, have no usable `creator_id`, so they all counted
against one address (127.0.0.1), and the sixth one inside a minute hit the 5-a-minute
limit. I re-ran both on their own after the window passed: each returns
`400 missing_creator_id`. That makes them HELD, but it shows the limiter can shadow other
tests, and that a person with no creator_id (or one behind a shared address) shares one
bucket with everybody else like them.

**Ten audit log entries from the run** (from `GET /log`, saved in
`results/audit_extract.json`; the full log is committed at `logs/audit.jsonl`). In order:
FP05, PI01, EV10, EV01, EV08, MF03, PI05, FP01, then a rate-limit rejection and a
rejected request with no creator_id.

```json
{"combined_score": 0.7083, "content_id": "4ec9c6f7de10", "creator_id": "attacker_FP05", "guess": "ai", "label": "This looks a lot like writing produced by an AI tool. Our check can be wrong, and if you wrote this yourself we would like to hear from you. You can ask for a review and a person will look at it.", "model_score": 0.8005, "status": "decided", "style_score": 0.616, "timestamp": "2026-11-21T08:34:41+00:00"}
{"combined_score": 0.2348, "content_id": "31df58e60335", "creator_id": "attacker_PI01", "guess": "human", "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.", "model_score": 0.4625, "status": "decided", "style_score": 0.0071, "timestamp": "2026-11-21T08:34:41+00:00"}
{"combined_score": 0.6, "content_id": "afe8e2dc5edc", "creator_id": "attacker_EV10", "guess": "unsure", "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.", "model_score": 0.9792, "status": "decided", "style_score": 0.3561, "timestamp": "2026-11-21T08:34:40+00:00"}
{"combined_score": 0.436, "content_id": "46fe0ac58a44", "creator_id": "attacker_EV01", "guess": "unsure", "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.", "model_score": 0.1635, "status": "decided", "style_score": 0.7086, "timestamp": "2026-11-21T08:34:40+00:00"}
{"combined_score": 0.2812, "content_id": "58f2c524eb71", "creator_id": "attacker_EV08", "guess": "human", "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.", "model_score": 0.2452, "status": "decided", "style_score": 0.3172, "timestamp": "2026-11-21T08:34:40+00:00"}
{"combined_score": 0.125, "content_id": "0270847f0712", "creator_id": "attacker_MF03", "guess": "human", "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.", "model_score": 0.0, "status": "decided", "style_score": 0.25, "timestamp": "2026-11-21T08:34:41+00:00"}
{"combined_score": 0.5594, "content_id": "f639fd1d02d4", "creator_id": "attacker_PI05", "guess": "unsure", "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.", "model_score": 0.6401, "status": "decided", "style_score": 0.4786, "timestamp": "2026-11-21T08:34:41+00:00"}
{"combined_score": 0.4821, "content_id": "b7c3d464adf5", "creator_id": "attacker_FP01", "guess": "unsure", "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.", "model_score": 0.6175, "status": "decided", "style_score": 0.3467, "timestamp": "2026-11-21T08:34:40+00:00"}
{"creator_id": "attacker_flood", "event": "rejected", "limit": "5 per 1 minute", "reason": "rate_limited", "status": "rejected", "timestamp": "2026-11-21T08:34:41+00:00"}
{"creator_id": "unknown", "event": "rejected", "reason": "missing_creator_id", "status": "rejected", "timestamp": "2026-11-21T08:34:41+00:00"}
```

**The single worst outcome** — the one I'd least want to explain to a writer whose work
got caught by it:

**FP05**, plain technical documentation written by a person ("To configure the service,
edit the settings file in the installation directory..."), came back as
`"guess": "ai"` with combined score 0.7083, so the writer would be told *"This looks a lot
like writing produced by an AI tool."* It is the only real person the set managed to
accuse. Both signals agreed (model 0.8005, style 0.616), so the disagreement guard, which
only acts when the signals split, never fired. Short, plain, imperative sentences are
exactly what a language model finds predictable, and my style signal does not
tell them apart from AI text. That is a diagnosis for Milestone 4; this is just what
happened.

---

## Run Log and Verdicts

Run with `python run_eval.py --label before` (`run_eval.py::main`, inputs in
`scenarios.py`), three trials with nothing changed in between. Full output:
`results/run_2026-11-21_0046_before.md`. The Run cells are counts made by `run_eval.py`; the verdicts are mine.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. My own writing flagged as AI | at most 2 of 10 labelled high-confidence AI, every trial | 1/10 ai, 5 unsure, 4 human | 1/10 ai, 5 unsure, 4 human | 1/10 ai, 5 unsure, 4 human | **MET** |
| 2. Score spread | AI average minus human average at least 0.30, every trial | AI 0.819 - human 0.359 = 0.460 | AI 0.819 - human 0.359 = 0.460 | AI 0.819 - human 0.359 = 0.460 | **MET** |
| 3. Bad input | 6 of 6 refused (400/413), no 500, each logged | 6/6 refused cleanly, 0 crashes, 6 logged | 6/6 refused cleanly, 0 crashes, 6 logged | 6/6 refused cleanly, 0 crashes, 6 logged | **MET** |
| 4a. Label coverage | all three labels appear in 10 varied submissions | 2/10 ai, 7 unsure, 1 human | 2/10 ai, 7 unsure, 1 human | 2/10 ai, 7 unsure, 1 human | **MET** |
| 4b. Score sweep | no gap or error from 0.00 to 1.00, and 0.51 and 0.95 differ | 101/101 labelled, 0 errors, 0.51 unsure vs 0.95 ai | same | same | **MET** |
| 5. Appeal path | 5 of 5 appeals return under_review and are logged, unknown id is a 404 | 5/5 appeals ok, unknown id -> 404 (ok=True) | 5/5 appeals ok, unknown id -> 404 (ok=True) | 5/5 appeals ok, unknown id -> 404 (ok=True) | **MET** |

**All three trials were identical for every criterion**, which is what I expected: neither
signal has any randomness, so the same text gets the same score. Nothing in the pipeline
was unstable.

**Where the text came from (this matters for criteria 1 and 2).** My "own writing" is ten
short emails I sent to schools and companies, copied word for word (`scenarios.py::MY_WRITING`).
They are 15 to 45 words long, far shorter than the roughly 300 words the detector was built
for, and one of them (piece 2, the on-campus jobs inquiry) reads formulaic, so I still have
to confirm I wrote it myself. The AI side of criterion 2 is five paragraphs an AI assistant
wrote in its usual style (`calibration_texts.py::AI_CLEAR`). The human side is five of my
own emails.

### How I decided each verdict

1. **MET, narrowly in spirit.** 1 of 10 labelled AI in every trial, against a limit of 2.
   The one it accused was piece 2 (combined 0.7933, model 0.868, style 0.719: both signals
   agreed, so the guard did not help). Only 4 of the 10 were called "human" and 5 were
   "unsure". Two caveats stop me calling this a clean pass: the pieces are very short, and
   if piece 2 is not really mine the count is 0 of 9.
2. **MET.** The gap was 0.460 (AI 0.819, human 0.359) against 0.30, in all three trials.
   The gap is probably flattering: my AI paragraphs are long and stock-phrase heavy, my
   human ones are short, and "interview thank-you" (0.591) was already in the unsure band.
3. **MET.** All six bad requests came back 400 or 413 with an `error` field, none crashed,
   and `GET /log` held six new `rejected` entries each trial.
4. **MET on both parts.** The ten varied inputs gave 2 ai, 7 unsure, 1 human in every trial,
   and the sweep had no gaps. But the "human" label showed up for only one input, so it is
   reachable and not much more. My criterion only asked for "at least once", which was a low bar.
5. **MET.** 5 of 5 appeals returned 200 `under_review`, each appears in the log with my
   exact reasoning, each original decision was still there and unchanged, and an appeal on an
   unknown id returned 404 and wrote nothing.

### What this says about my criteria

**I held all five, and I should say plainly that my targets were low.** The attack set broke
14 of 56 attacks against a service that "passes" every criterion I wrote. The criteria tested
things the service is good at (refusing empty input, recording appeals) or measured with
generous inputs. The ones I would tighten:

- **Criterion 1.** At most 2 in 10 is 20% of real writers accused. And it passed using texts
  too short for the detector to judge. It should be run on writing of at least 100 words.
- **Criterion 2.** AI-clear against human-clear says nothing about AI text that has been
  disguised. A better version would be a spread between lightly edited AI text and plain human.
- **Criterion 4a.** "Each label at least once" would pass if the human label were reachable
  by a single input. It should say how many of the ten human pieces get the human label.

None of the criteria was unmeasurable, so I am not revising any of them. `criteria.md` is unchanged.

**Real output from one trial** (`run_eval.py::run_texts_or_bodies`, `run_spread`, `run_sweep`,
`run_appeal`, trial 1 of `results/run_2026-11-21_0046_before.md`). The long `label` sentence is shortened to its first
words; everything else is as returned.

Criterion 1, `app.py::submit` for each of my ten pieces:

```json
{"status": 200, "guess": "unsure", "confidence": 0.5909, "model_score": 0.8961, "style_score": 0.2858, "label": "We couldn't tell whether this was ...", "error": null, "sent": "Thank you so much for taking time to interview me today! It was a plea"}
{"status": 200, "guess": "ai", "confidence": 0.7933, "model_score": 0.8677, "style_score": 0.7189, "label": "This looks a lot like writing prod...", "error": null, "sent": "I am writing to inquire about potential on-campus employment opportuni"}
{"status": 200, "guess": "unsure", "confidence": 0.4291, "model_score": 0.4067, "style_score": 0.4514, "label": "We couldn't tell whether this was ...", "error": null, "sent": "I am not sure how to register for Sparta camp. I dont see it anywhere "}
{"status": 200, "guess": "human", "confidence": 0.2979, "model_score": 0.1436, "style_score": 0.4522, "label": "We think this was probably written...", "error": null, "sent": "I applied for Data Analytics for fall 2025 in October 2024, but have n"}
{"status": 200, "guess": "unsure", "confidence": 0.6, "model_score": 0.2987, "style_score": 0.9157, "label": "We couldn't tell whether this was ...", "error": null, "sent": "Actually i am planning to apply for fall 2025. Do you know when can i "}
{"status": 200, "guess": "human", "confidence": 0.2607, "model_score": 0.042, "style_score": 0.4795, "label": "We think this was probably written...", "error": null, "sent": "Just saw the MySJSU portal. There is enrollment appointment date avail"}
{"status": 200, "guess": "human", "confidence": 0.2923, "model_score": 0.2345, "style_score": 0.35, "label": "We think this was probably written...", "error": null, "sent": "Thanks for sending this over. In Education section should we add upcom"}
{"status": 200, "guess": "unsure", "confidence": 0.4596, "model_score": 0.3173, "style_score": 0.6018, "label": "We couldn't tell whether this was ...", "error": null, "sent": "Wanted to check if my resume is optimised or not? When will the market"}
{"status": 200, "guess": "unsure", "confidence": 0.4851, "model_score": 0.3703, "style_score": 0.6, "label": "We couldn't tell whether this was ...", "error": null, "sent": "Is my resume being submitted for a specific open role, or is this gene"}
{"status": 200, "guess": "human", "confidence": 0.3531, "model_score": 0.1796, "style_score": 0.5266, "label": "We think this was probably written...", "error": null, "sent": "I am writing this to know does Data analytics (special session) offer "}
```

Criterion 2, the ten texts behind the spread (`group` is added by `run_eval.py`):

```json
{"status": 200, "guess": "ai", "confidence": 0.7498, "model_score": 0.822, "style_score": 0.6777, "label": "This looks a lot like writing prod...", "error": null, "sent": "Artificial intelligence is transforming the way businesses operate in ", "group": "ai"}
{"status": 200, "guess": "ai", "confidence": 0.783, "model_score": 0.9328, "style_score": 0.6331, "label": "This looks a lot like writing prod...", "error": null, "sent": "Regular exercise offers numerous benefits for both physical and mental", "group": "ai"}
{"status": 200, "guess": "ai", "confidence": 0.9066, "model_score": 0.9556, "style_score": 0.8576, "label": "This looks a lot like writing prod...", "error": null, "sent": "Climate change is one of the most pressing challenges facing our plane", "group": "ai"}
{"status": 200, "guess": "ai", "confidence": 0.8304, "model_score": 0.7932, "style_score": 0.8675, "label": "This looks a lot like writing prod...", "error": null, "sent": "Effective communication is a fundamental skill in both personal and pr", "group": "ai"}
{"status": 200, "guess": "ai", "confidence": 0.8253, "model_score": 0.9241, "style_score": 0.7264, "label": "This looks a lot like writing prod...", "error": null, "sent": "The history of the internet is a fascinating journey that spans severa", "group": "ai"}
{"status": 200, "guess": "unsure", "confidence": 0.5909, "model_score": 0.8961, "style_score": 0.2858, "label": "We couldn't tell whether this was ...", "error": null, "sent": "Thank you so much for taking time to interview me today! It was a plea", "group": "human"}
{"status": 200, "guess": "human", "confidence": 0.2979, "model_score": 0.1436, "style_score": 0.4522, "label": "We think this was probably written...", "error": null, "sent": "I applied for Data Analytics for fall 2025 in October 2024, but have n", "group": "human"}
{"status": 200, "guess": "human", "confidence": 0.2607, "model_score": 0.042, "style_score": 0.4795, "label": "We think this was probably written...", "error": null, "sent": "Just saw the MySJSU portal. There is enrollment appointment date avail", "group": "human"}
{"status": 200, "guess": "human", "confidence": 0.2923, "model_score": 0.2345, "style_score": 0.35, "label": "We think this was probably written...", "error": null, "sent": "Thanks for sending this over. In Education section should we add upcom", "group": "human"}
{"status": 200, "guess": "human", "confidence": 0.3531, "model_score": 0.1796, "style_score": 0.5266, "label": "We think this was probably written...", "error": null, "sent": "I am writing this to know does Data analytics (special session) offer ", "group": "human"}
```

Criterion 3, `app.py::submit` and `app.py::_check_input` for the six bad requests:

```json
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "label": null, "error": "missing_text", "sent": "{\"creator_id\": \"eval_bad_a\"}"}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "label": null, "error": "empty_text", "sent": "(empty text)"}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "label": null, "error": "empty_text", "sent": "     "}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "label": null, "error": "text_not_a_string", "sent": "{\"text\": 12345, \"creator_id\": \"eval_bad_d\"}"}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "label": null, "error": "missing_creator_id", "sent": "{\"text\": \"Real writing here.\"}"}
{"status": 413, "guess": null, "confidence": null, "model_score": null, "style_score": null, "label": null, "error": "text_too_long", "sent": "word word word word word word word word word word word word word word "}
```

Criterion 4, ten varied inputs, then the sweep (`scoring.py::score_to_label`):

```json
{"status": 200, "guess": "ai", "confidence": 0.7498, "model_score": 0.822, "style_score": 0.6777, "label": "This looks a lot like writing prod...", "error": null, "sent": "Artificial intelligence is transforming the way businesses operate in "}
{"status": 200, "guess": "ai", "confidence": 0.783, "model_score": 0.9328, "style_score": 0.6331, "label": "This looks a lot like writing prod...", "error": null, "sent": "Regular exercise offers numerous benefits for both physical and mental"}
{"status": 200, "guess": "unsure", "confidence": 0.5909, "model_score": 0.8961, "style_score": 0.2858, "label": "We couldn't tell whether this was ...", "error": null, "sent": "Thank you so much for taking time to interview me today! It was a plea"}
{"status": 200, "guess": "unsure", "confidence": 0.4291, "model_score": 0.4067, "style_score": 0.4514, "label": "We couldn't tell whether this was ...", "error": null, "sent": "I am not sure how to register for Sparta camp. I dont see it anywhere "}
{"status": 200, "guess": "human", "confidence": 0.3354, "model_score": 0.4469, "style_score": 0.2239, "label": "We think this was probably written...", "error": null, "sent": "Okay so my landlord finally fixed the heater, three weeks after I aske"}
{"status": 200, "guess": "unsure", "confidence": 0.6, "model_score": 0.8461, "style_score": 0.4199, "label": "We couldn't tell whether this was ...", "error": null, "sent": "I went to the park with my dog on Saturday. It was a nice day and a lo"}
{"status": 200, "guess": "unsure", "confidence": 0.4763, "model_score": 0.7442, "style_score": 0.2085, "label": "We couldn't tell whether this was ...", "error": null, "sent": "My favorite season is summer. I like it because the days are long and "}
{"status": 200, "guess": "unsure", "confidence": 0.5888, "model_score": 0.5166, "style_score": 0.661, "label": "We couldn't tell whether this was ...", "error": null, "sent": "The treaty, ratified in the long shadow of a war that had exhausted ev"}
{"status": 200, "guess": "unsure", "confidence": 0.4902, "model_score": 0.4461, "style_score": 0.5343, "label": "We couldn't tell whether this was ...", "error": null, "sent": "Artifical intelligence is changing how people work and I think thats m"}
{"status": 200, "guess": "unsure", "confidence": 0.5118, "model_score": 0.6655, "style_score": 0.3581, "label": "We couldn't tell whether this was ...", "error": null, "sent": "Exercise has loads of benefits for body and mind, which i found out af"}
{"status": "n/a", "sent": "scores 0.00 to 1.00 in steps of 0.01", "errors": 0, "labels_seen": ["ai", "human", "unsure"], "label_at_0.51": "unsure", "label_at_0.95": "ai"}
```

Criterion 5, `app.py::appeal` and `audit.py::log_appeal` (the last line is the unknown id):

```json
{"sent": "appeal on submission 1", "content_id": "55009f8301db", "status": 200, "appeal_status": "under_review", "appeal_logged": true, "decision_intact": true, "passed": true}
{"sent": "appeal on submission 2", "content_id": "9f49b5c217d4", "status": 200, "appeal_status": "under_review", "appeal_logged": true, "decision_intact": true, "passed": true}
{"sent": "appeal on submission 3", "content_id": "ccc1357e730d", "status": 200, "appeal_status": "under_review", "appeal_logged": true, "decision_intact": true, "passed": true}
{"sent": "appeal on submission 4", "content_id": "5fb7c47747fb", "status": 200, "appeal_status": "under_review", "appeal_logged": true, "decision_intact": true, "passed": true}
{"sent": "appeal on submission 5", "content_id": "2182954d37d8", "status": 200, "appeal_status": "under_review", "appeal_logged": true, "decision_intact": true, "passed": true}
{"sent": "appeal on unknown content_id", "status": 404, "appeal_entry_written": false, "passed": true}
```

### Diagnoses of the 14 attacks that broke

My criteria had no misses, so these are the attacks from Attack Run — Before. The service has
five stages: the route (`app.py::submit`), signal one (`detector.py::model_signal`), signal two
(`stylometry.py::style_signal`), the combining rule (`scoring.py::combine_signals`) and the label
mapping (`scoring.py::score_to_label`). Scores below are model / style / combined.

**Pattern A, signal two reads sentence-length spread, and anything that changes sentence length
fools it. This is 6 of the 14 (EV02, EV03, EV06, EV09, PI01, PI02).** Signal two gives half its
weight to `sentence_length_spread`, where lumpy sentences mean human.
- *EV02* (broken-up sentences, 0.594 / 0.274 / 0.434) and *EV06* (one very long and one very short
  sentence, 0.573 / 0.249 / 0.411): the edit creates exactly the uneven sentence lengths that mean
  "human" to this signal, so style fell to about 0.25.
- *EV03* (a pasted quotation, 0.666 / 0.478 / 0.572) and *EV09* (a human opening bolted on,
  0.704 / 0.433 / 0.569): the added material has different sentence lengths from the AI text
  around it, which dilutes the style score. In both, signal one still said "AI" (0.67, 0.70); it
  was the 0.5 weight on a fooled signal two that pulled the average down into unsure.
- *PI01* (0.462 / 0.007 / 0.235) and *PI02* (0.204 / 0.222 / 0.213): these look like prompt
  injection, but the service never reads instructions; it has no part that could obey one. What
  worked is that "Ignore all previous instructions..." and "SYSTEM: ..." add short sentences in
  front of long AI ones, which pushes the sentence-length spread up and style to nearly 0.
  So this is the same mechanism as EV02, not a different attack. The stage is signal two.

**Pattern B, the route accepts text that is too short or is not text, and signal one answers
"human" for it. This is 3 of the 14 (EV08, MF03, MF04).** `app.py::_check_input` only checks that
text is a non-empty string, and `detector.model_signal` only rejects one or two tokens.
- *EV08* (65 characters, 0.245 / 0.317 / 0.281): ten words is below what either signal can read, but
  the route lets it through and the score looks confident.
- *MF03* (control characters, 0.0 / 0.25 / 0.125) and *MF04* (only punctuation, 0.011 / 0.5 / 0.256):
  the model finds nothing to predict, so model_score is about 0, and the average says "human".
  Junk is being cleared as human. The stage is the route (no check that there are enough real
  words), and signal one is how it shows.

**Pattern C, the disagreement guard cuts both ways (EV10).** EV10 (a
paragraph repeated 3 times, 0.979 / 0.356 / 0.600): signal one was nearly certain (0.98), but
style was low, the signals were 0.62 apart, and the guard capped the score at exactly 0.60, which
is "unsure". Without the guard the plain average is 0.668, "high-confidence AI", and the attack
would have been caught. I checked every one of the 56 attacks: the guard changed a label in only
three (EV10, MF06 and MF07, all from "ai" to "unsure"), and it saved **none** of the eight
false-positive attacks, because their plain averages were already at or under 0.60. I built it
from a single calibration paragraph. Its effect on this set is one attack let through (EV10)
and two junk inputs kept from being called AI (MF06, MF07). The stage is the combining rule.

**Single cases that don't fit a pattern:**
- *EV01* (typos, 0.164 / 0.709 / 0.436): the attack set labelled this a signal two attack, but signal
  two still said "AI" (0.709). It was signal one that was fooled: misspelled words are rare tokens,
  gpt2 finds them surprising, and model_score dropped to 0.16. This is the typo case I predicted in
  my README, on the wrong signal. The stage is signal one.
- *EV07* (punctuation padding, 0.586 / 0.676 / 0.631): the combined score was 0.019 under the AI
  threshold of 0.65. Whatever padding did, the stage that decided it is the label mapping: one
  small threshold move would flip it. It is a near miss, not a clear break.
- *EV05* (heavy human edit, 0.321 / 0.428 / 0.374): both signals read "human". A text that has been
  rewritten heavily by a person may reasonably look human, so I count this as the least convincing
  of the 14, and I would not try to fix it.
- *FP05* (a person's technical documentation, 0.800 / 0.616 / 0.708): short imperative sentences are
  predictable to gpt2 and uniform in length, so both signals said AI and the guard (which only acts
  when the signals split) never fired. The stage is both signals at once. This is the false positive
  the unit warns about, and it is my worst outcome.

So the 14 come down to three problems: signal two can be moved by anything that changes sentence
lengths (6), the route lets in text that is too short or is not text (3), and the combining rule
and the signals are each weak in their own way (5 single cases: EV01, EV05, EV07, EV10, FP05).

---

## The Improvement

**What I changed:** One thing: **input validation on the route.** `/submit` now refuses any
text with fewer than 12 real words, with a 400 and the reason `not_enough_text`, and logs the
refusal like the other bad inputs. A "word" is a run of letters, so punctuation, digits, emoji
and control characters count as zero. The code is `app.py::_check_input` (using the new helper
`app.py::_count_words`) and the number is `config.py::MIN_WORDS = 12`. I changed nothing else:
no signal, weight, threshold or label.

**Which diagnosis pointed at it:** Pattern B in Run Log and Verdicts: the route accepted text that
was too short or was not text, and signal one answered "human" for it (EV08, MF03, MF04). It was
the cleanest place to start for two reasons. It removes a wrong answer instead of moving a
threshold, so it cannot push a real writer toward "AI". And the alternative with the biggest
payoff, reweighting signal two (Pattern A, 6 attacks), would pull plain human writing toward
"AI", which is the mistake my criteria say is the expensive one. I chose 12 because it is above
the attack set's 10-word EV08 and below the shortest of my own emails (16 words).

### Attack Run — After

Run with `python run_attacks.py --set attack_set --label after`, same service, same marking rule
as before. Full output: `results/attack_run_2026-11-21_0058_after.md`. `*` = RQ10 and RQ11 came back
429 from my own limiter in both full runs (the same effect as before); run alone after the
window passed, both return 400 both times. `←` marks the 11 rows that changed.

| Family | Held before | Broke before | Held after | Broke after |
|---|---|---|---|---|
| evasion (10) | 1 | 9 | 2 | 8 |
| false_positive (8) | 7 | 1 | 7 | 1 |
| prompt_injection (6) | 4 | 2 | 4 | 2 |
| malformed (20) | 18 | 2 | 20 | 0 |
| flood_same_creator (12) | 12 | 0 | 12 | 0 |
| **Total (56)** | **42** | **14** | **45** | **11** |

| ID | Family | Before: status, guess, score | Mark | After: status, guess, score | Mark |
|---|---|---|---|---|---|
| EV01 | evasion | 200 unsure 0.436 | BROKE | 200 unsure 0.436 | BROKE |
| EV02 | evasion | 200 unsure 0.434 | BROKE | 200 unsure 0.434 | BROKE |
| EV03 | evasion | 200 unsure 0.572 | BROKE | 200 unsure 0.572 | BROKE |
| EV04 | evasion | 200 ai 0.681 | HELD | 200 ai 0.681 | HELD |
| EV05 | evasion | 200 human 0.374 | BROKE | 200 human 0.374 | BROKE |
| EV06 | evasion | 200 unsure 0.411 | BROKE | 200 unsure 0.411 | BROKE |
| EV07 | evasion | 200 unsure 0.631 | BROKE | 200 unsure 0.631 | BROKE |
| EV08 | evasion | 200 human 0.281 | BROKE | 400 — — ← | HELD |
| EV09 | evasion | 200 unsure 0.569 | BROKE | 200 unsure 0.569 | BROKE |
| EV10 | evasion | 200 unsure 0.600 | BROKE | 200 unsure 0.600 | BROKE |
| FP01 | false_positive | 200 unsure 0.482 | HELD | 200 unsure 0.482 | HELD |
| FP02 | false_positive | 200 unsure 0.633 | HELD | 200 unsure 0.633 | HELD |
| FP03 | false_positive | 200 unsure 0.587 | HELD | 200 unsure 0.587 | HELD |
| FP04 | false_positive | 200 unsure 0.600 | HELD | 200 unsure 0.600 | HELD |
| FP05 | false_positive | 200 ai 0.708 | BROKE | 200 ai 0.708 | BROKE |
| FP06 | false_positive | 200 unsure 0.566 | HELD | 200 unsure 0.566 | HELD |
| FP07 | false_positive | 200 unsure 0.600 | HELD | 200 unsure 0.600 | HELD |
| FP08 | false_positive | 200 human 0.245 | HELD | 400 — — ← | HELD |
| PI01 | prompt_injection | 200 human 0.235 | BROKE | 200 human 0.235 | BROKE |
| PI02 | prompt_injection | 200 human 0.213 | BROKE | 200 human 0.213 | BROKE |
| PI03 | prompt_injection | 200 unsure 0.571 | HELD | 200 unsure 0.571 | HELD |
| PI04 | prompt_injection | 200 unsure 0.545 | HELD | 200 unsure 0.545 | HELD |
| PI05 | prompt_injection | 200 unsure 0.559 | HELD | 200 unsure 0.559 | HELD |
| PI06 | prompt_injection | 200 unsure 0.448 | HELD | 200 unsure 0.448 | HELD |
| MF01 | malformed | 400 — — | HELD | 400 — — | HELD |
| MF02 | malformed | 400 — — | HELD | 400 — — | HELD |
| MF03 | malformed | 200 human 0.125 | BROKE | 400 — — ← | HELD |
| MF04 | malformed | 200 human 0.256 | BROKE | 400 — — ← | HELD |
| MF05 | malformed | 200 unsure 0.600 | HELD | 400 — — ← | HELD |
| MF06 | malformed | 200 unsure 0.600 | HELD | 400 — — ← | HELD |
| MF07 | malformed | 200 unsure 0.600 | HELD | 200 unsure 0.600 | HELD |
| MF08 | malformed | 413 — — | HELD | 413 — — | HELD |
| RQ01 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ02 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ03 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ04 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ05 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ06 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ07 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ08 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ09 | malformed | 400 — — | HELD | 400 — — | HELD |
| RQ10 | malformed | 400* — — | HELD | 400* — — | HELD |
| RQ11 | malformed | 400* — — | HELD | 400* — — | HELD |
| RQ12 | malformed | 400 — — | HELD | 400 — — | HELD |
| FL01_01 | flood_same_creator | 200 human 0.139 | HELD | 400 — — ← | HELD |
| FL01_02 | flood_same_creator | 200 human 0.139 | HELD | 400 — — ← | HELD |
| FL01_03 | flood_same_creator | 200 human 0.139 | HELD | 400 — — ← | HELD |
| FL01_04 | flood_same_creator | 200 human 0.139 | HELD | 400 — — ← | HELD |
| FL01_05 | flood_same_creator | 200 human 0.139 | HELD | 400 — — ← | HELD |
| FL01_06 | flood_same_creator | 429 — — | HELD | 429 — — | HELD |
| FL01_07 | flood_same_creator | 429 — — | HELD | 429 — — | HELD |
| FL01_08 | flood_same_creator | 429 — — | HELD | 429 — — | HELD |
| FL01_09 | flood_same_creator | 429 — — | HELD | 429 — — | HELD |
| FL01_10 | flood_same_creator | 429 — — | HELD | 429 — — | HELD |
| FL01_11 | flood_same_creator | 429 — — | HELD | 429 — — | HELD |
| FL01_12 | flood_same_creator | 429 — — | HELD | 429 — — | HELD |

The five criteria were run again (`python run_eval.py --label after`, `results/run_2026-11-21_0100_after.md`):
**all identical to before, in all three trials, all still MET** (1 of 10 accused, spread 0.460, 6 of 6
bad requests refused and logged, labels 2 ai / 7 unsure / 1 human, appeals 5 of 5).

**Did it help, and how do I know:** **Yes, a little: 14 attacks broke before and 11 break now.**
Three moved from BROKE to HELD: EV08 (a 10-word AI text no longer gets a confident "human"), MF03
(control characters) and MF04 (only punctuation) are now refused with a 400. Every row that did
not change status has exactly the same guess and score as before (I checked this in code), so
nothing else moved. The 8 evasion and 2 injection attacks that still break were never about short text and
did not change at all.

What it costs, and what it does not fix:
- **It refuses some real writing.** FP08 ("Went for a run. Legs hurt. Worth it.", 8 words) was a
  genuine human text that used to get "human" and now gets a 400 asking for 12 words. I still
  mark it HELD because nobody was accused, but that writer gets no answer. A caption, a poem or a
  one-line reply is refused. A refusal is the honest answer to "not enough to judge", but it is
  a cost, and it falls on writers of short pieces.
- **Seven other attacks went from a score to a refusal** without being detected: MF05 and MF06 (a long
  single word, emoji) used to come back "unsure" and are now refused, and the five flood-text rows
  FL01_01 to FL01_05 (9 words) used to be scored "human" and are now 400s. The flood is still
  stopped on the sixth request with a 429, so that test still works, but it no longer exercises
  the model.
- **It is easy to get around.** EV08 is "held" because it was refused, not because it was caught.
  Someone who wants an AI sentence scored just has to write 12 words.
- **It did nothing for the real accusation.** FP05 (a real person's docs, 0.708, "ai") and the
  signal-two attacks are unchanged.

So the one-sentence answer: it removed three wrong "human" answers at the cost of refusing short
writing, and left the two failures that matter most (a real person accused, and AI text that
changes its sentence lengths) exactly where they were.

---

## What's Still Broken

**The 11 attacks that still break**, what I'd do about each, and why I stopped:

| Attack | What I'd do | Why I stopped |
|---|---|---|
| EV02, EV03, EV06, EV09, PI01, PI02 (signal two reads sentence-length spread) | Lower the weight on `sentence_length_spread` in `stylometry.py` (now 0.50), or score the text in chunks so one odd sentence cannot move the whole score. | Only one change was allowed. And the cost is direct: plain human writing already looks "even" to this signal, so shifting weight away from it makes real writers look more like AI. I would want my own 100-word-plus writing to test it on before touching it. |
| EV01 (typos fool signal one) | Strip or normalise obvious misspellings before scoring with gpt2. | Hard to do without also altering real writing: second-language writers and fast typists make the same errors, and "fixing" them changes the text being judged. |
| EV05 (heavy human edit, "human" 0.374) | Nothing. | A text that a person rewrote heavily may honestly look human. I do not count this as a real failure. |
| EV07 (0.631, 0.019 under the AI line) | Lower `AI_THRESHOLD` from 0.65 to about 0.62. | It would catch EV07 but also accuse FP02, a real person's formal writing at 0.633. One more accusation for one more catch is a bad trade for a writing site, so I left the line where it is. |
| EV10 (repeated AI paragraph, capped to 0.600 by the guard) | Skip the disagreement guard when the model signal alone is very high (for example above 0.95). | The guard only helped MF06 and MF07 here (junk labelled AI without it), and those two are now mostly covered by the validation. Dropping it would be defensible, but it was the one rule I built to protect real writers, and I have no evidence yet that it never hurts them. |
| FP05 (a real person's technical docs accused, 0.708) | Raise `AI_THRESHOLD` above 0.71, or send every "ai" label to a human reviewer first. | Raising the line also lets EV04 (0.681), the one evasion that is currently caught, go through. The honest fix is not a threshold: both signals read short, plain, imperative sentences as AI, and I do not have a third signal that can tell the difference. Until I do, "ai" should be a reason to look, not a verdict. |

**Also still broken, outside the attack count:**
- **The rate limit counts by `creator_id`, which a caller types**, so a script can dodge it by changing the id on every request. And requests with no usable `creator_id` all share one address bucket, which is why RQ10 and RQ11 came back 429 on a full run. A fix needs ids the service issues, not ones the caller supplies.
- **The human label is hard to reach.** In my own writing only 4 of 10 pieces got it, and among ten varied inputs only 1 did. Most real writing lands in "unsure", which is safe but means the system rarely says anything useful.
- **My criteria were too easy** (see Run Log and Verdicts): I would rerun criterion 1 on 100-word-plus writing, criterion 2 on lightly edited AI text, and criterion 4a with a minimum number of "human" labels.
- **Everything is tested on English only**, and the model is gpt2. MF07 (Arabic) was accepted and scored "unsure", but I have no reason to think the signals mean anything for it.

**The trade I'd make if this ran for real:** I would accept more AI text getting through. A wrongly accused writer loses trust and may lose work, while a missed AI piece costs the site very little, so I would keep the "AI" line high (0.65 or higher, never lower) and treat "unsure" as normal. The people who pay for that choice are the other writers and readers on the site, who sometimes read undisclosed AI text, and the writers whose short or plain pieces get "unsure" or a refusal when they only wanted an answer.

---

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
