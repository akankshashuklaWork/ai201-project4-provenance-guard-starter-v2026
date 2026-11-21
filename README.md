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

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



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
