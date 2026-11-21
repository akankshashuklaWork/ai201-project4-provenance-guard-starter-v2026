# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---

> **Authorship note (disclosed in the README's "How I Used AI").** The targets
> below are my choices: I picked the false-positive rate (at most 2 in 10),
> the score spread (0.30), the bad-input rule (400 and logged, never a 500),
> and the areas covered. The exact wording and the "why" paragraphs were
> drafted by an AI assistant from those choices, before any of the code
> existed. I reviewed them and they are my standard. Written and committed
> BEFORE the service was built, so no result could have shaped them.

Every criterion is checked **across three trials** of the same inputs, and the
target has to hold in all three (the first signal is a model, so the same text
can score slightly differently twice).

---

## 1. False positives: at most 2 in 10 human pieces called AI

Of 10 pieces of plain, ordinary writing by real people (not formal, not
polished by a tool), **at most 2** may receive the *high-confidence AI* label.
This must hold in **each** of three trials of the same ten pieces.

**Why this target:** Accusing a real writer is the expensive mistake. They lose
trust and may lose the work. Missing a piece of AI text costs the site very
little. 2 in 10 is looser than I'd like and I know it: both of my signals are
weak (a small local model and a count of sentence shapes), and plain human
writing is exactly the kind they misread. I'm choosing a number I can honestly
hit and then checking it, rather than a 0-in-10 I would miss. The unsure band
and the appeal path are what make even this rate bearable, because a writer who
is wrongly flagged can answer back.

---

## 2. Score spread: clearly-AI and clearly-human text score at least 0.30 apart

Take 5 pieces I'm sure are AI-written and 5 I'm sure are human-written. The
**average combined score** of the AI set minus the average of the human set
must be **at least 0.30**, in each of three trials.

**Why this target:** If the two groups barely differ, the score is noise and the
labels mean nothing. 0.30 is about the width of the "unsure" band, so it means
the two groups at least land in different regions. It is deliberately not 0.50:
two weak signals averaged will not give a huge gap, and a target I can't
plausibly reach tells me nothing.

---

## 3. Bad input: nothing crashes, everything refused is logged

Send `/submit` six bad requests: (a) no `text` field, (b) `text` is empty,
(c) `text` is only spaces, (d) `text` is a number instead of a string,
(e) no `creator_id`, (f) `text` of 50,000 characters. **All six** must return
HTTP 400 (413 for the oversized one) with a JSON body containing an `error`
field, **none** may return a 500, and **each** must leave a `rejected` entry in
`logs/audit.jsonl`. 6 of 6, in all three trials.

**Why this target:** A crash on malformed input is one of the most common real
failures, and a refusal that leaves no trace looks the same as a quiet
afternoon. "Never a 500" is something anyone can check by running six curl
commands. The log requirement is there because next unit I need to be able to
see what was thrown at the service.

---

## 4. Label coverage: all three labels are reachable, and the score actually matters

(a) Across 10 varied submissions (AI, human, plain, formal, edited AI), **each
of the three labels appears at least once.** (b) Sweeping every score from 0.00
to 1.00 in steps of 0.01 through `score_to_label` produces **no gap and no
error**, and a score of **0.51 and a score of 0.95 produce different labels**.

**Why this target:** A label nobody can ever see is dead code, and a system
that flips at 0.5 isn't expressing confidence at all. Part (b) can be checked
without the model, so it can't pass by luck. Part (a) catches the more
likely failure: ranges that look fine on paper but a combined score that never
actually leaves the middle.

---

## 5. Appeal path: every appeal changes status and is recorded

For 5 submissions, send an appeal on each real `content_id`. **All 5** must
return HTTP 200 with `status: "under_review"`, and `GET /log` must then show,
for each one, an appeal entry holding the writer's exact reasoning **and** the
original decision entry still present and unchanged. An appeal on a
`content_id` that doesn't exist must return 404 and write no appeal entry.
5 of 5, in all three trials.

**Why this target:** The appeal is the only thing standing between a wrong
accusation and nothing at all, so it is the one path that should have no
failures. 5 of 5 isn't generous, it's the baseline: an appeal that sometimes
vanishes is worse than no appeal, because the writer thinks someone is looking.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
