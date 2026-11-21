# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-21 00:34
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `46fe0ac58a44` | unsure | 0.436 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `d3f12702ba2f` | unsure | 0.434 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `8bdc5dd6cab3` | unsure | 0.572 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `15bac51298f1` | ai | 0.681 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `e7e70a06fc37` | human | 0.374 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `bec93545f520` | unsure | 0.411 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `d52b14c410f1` | unsure | 0.631 |  |
| EV08 | evasion | signal one: text below the token window | 200 | `58f2c524eb71` | human | 0.281 |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `f5b82d911e9b` | unsure | 0.569 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `afe8e2dc5edc` | unsure | 0.600 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `b7c3d464adf5` | unsure | 0.482 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `d8547c830a56` | unsure | 0.633 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `92e861b7afe1` | unsure | 0.587 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `1616d88b1661` | unsure | 0.600 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `4ec9c6f7de10` | ai | 0.708 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `fdd412630ef1` | unsure | 0.566 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `04f48c20cc17` | unsure | 0.600 |  |
| FP08 | false_positive | very short genuine human submission | 200 | `10e32c96118d` | human | 0.245 |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `31df58e60335` | human | 0.235 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `792be35920d6` | human | 0.213 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `27207fcd51b7` | unsure | 0.571 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `edf9c2fb97c5` | unsure | 0.545 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `f639fd1d02d4` | unsure | 0.559 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `54181b303a3e` | unsure | 0.448 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 200 | `0270847f0712` | human | 0.125 |  |
| MF04 | malformed | text is only punctuation | 200 | `aeeec0ba74af` | human | 0.256 |  |
| MF05 | malformed | text is a very long single word | 200 | `3dc43e1dc924` | unsure | 0.600 |  |
| MF06 | malformed | text is emoji only | 200 | `828cfd339833` | unsure | 0.600 |  |
| MF07 | malformed | text is right-to-left script | 200 | `e592ec0afb29` | unsure | 0.600 |  |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `fa921c360261` | human | 0.139 |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `542bb5d39608` | human | 0.139 |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `92b13568a849` | human | 0.139 |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `ec94e45ffe62` | human | 0.139 |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `fdeb3fd2d7f9` | human | 0.139 |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "46fe0ac58a44",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.436,
  "model_score": 0.1635,
  "style_score": 0.7086,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "d3f12702ba2f",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.434,
  "model_score": 0.5943,
  "style_score": 0.2737,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "8bdc5dd6cab3",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.5722,
  "model_score": 0.6662,
  "style_score": 0.4782,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "15bac51298f1",
  "creator_id": "attacker_EV04",
  "guess": "ai",
  "confidence": 0.6807,
  "model_score": 0.6114,
  "style_score": 0.7501,
  "label": "This looks a lot like writing produced by an AI tool. Our check can be wrong, and if you wrote this yourself we would like to hear from you. You can ask for a review and a person will look at it.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "e7e70a06fc37",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.3745,
  "model_score": 0.3212,
  "style_score": 0.4279,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "bec93545f520",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.4108,
  "model_score": 0.5727,
  "style_score": 0.2488,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "d52b14c410f1",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.631,
  "model_score": 0.5862,
  "style_score": 0.6758,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "58f2c524eb71",
  "creator_id": "attacker_EV08",
  "guess": "human",
  "confidence": 0.2812,
  "model_score": 0.2452,
  "style_score": 0.3172,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "f5b82d911e9b",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.5685,
  "model_score": 0.7042,
  "style_score": 0.4327,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "afe8e2dc5edc",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.9792,
  "style_score": 0.3561,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "b7c3d464adf5",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.4821,
  "model_score": 0.6175,
  "style_score": 0.3467,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "d8547c830a56",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.6334,
  "model_score": 0.7387,
  "style_score": 0.5281,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "92e861b7afe1",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.5871,
  "model_score": 0.8051,
  "style_score": 0.3691,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "1616d88b1661",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.8329,
  "style_score": 0.3674,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "4ec9c6f7de10",
  "creator_id": "attacker_FP05",
  "guess": "ai",
  "confidence": 0.7083,
  "model_score": 0.8005,
  "style_score": 0.616,
  "label": "This looks a lot like writing produced by an AI tool. Our check can be wrong, and if you wrote this yourself we would like to hear from you. You can ask for a review and a person will look at it.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "fdd412630ef1",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.5664,
  "model_score": 0.8814,
  "style_score": 0.2514,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "04f48c20cc17",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.8816,
  "style_score": 0.3195,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "10e32c96118d",
  "creator_id": "attacker_FP08",
  "guess": "human",
  "confidence": 0.2446,
  "model_score": 0.3223,
  "style_score": 0.167,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "31df58e60335",
  "creator_id": "attacker_PI01",
  "guess": "human",
  "confidence": 0.2348,
  "model_score": 0.4625,
  "style_score": 0.0071,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "792be35920d6",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.2133,
  "model_score": 0.2044,
  "style_score": 0.2222,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "27207fcd51b7",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.5708,
  "model_score": 0.5943,
  "style_score": 0.5472,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "edf9c2fb97c5",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.5453,
  "model_score": 0.4998,
  "style_score": 0.5907,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "f639fd1d02d4",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.5594,
  "model_score": 0.6401,
  "style_score": 0.4786,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "54181b303a3e",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.4478,
  "model_score": 0.5583,
  "style_score": 0.3373,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 200,
  "content_id": "0270847f0712",
  "creator_id": "attacker_MF03",
  "guess": "human",
  "confidence": 0.125,
  "model_score": 0.0,
  "style_score": 0.25,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 200,
  "content_id": "aeeec0ba74af",
  "creator_id": "attacker_MF04",
  "guess": "human",
  "confidence": 0.2556,
  "model_score": 0.0112,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 200,
  "content_id": "3dc43e1dc924",
  "creator_id": "attacker_MF05",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.9976,
  "style_score": 0.25,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 200,
  "content_id": "828cfd339833",
  "creator_id": "attacker_MF06",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.9969,
  "style_score": 0.5,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "e592ec0afb29",
  "creator_id": "attacker_MF07",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.9064,
  "style_score": 0.5,
  "label": "We couldn't tell whether this was written by a person or with the help of an AI tool, and we haven't made a judgement about it. Our checks can't always tell, especially with plain, simple writing, so please don't read anything into this. If you'd like someone to take a look, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "fa921c360261",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1394,
  "model_score": 0.0287,
  "style_score": 0.25,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "542bb5d39608",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1394,
  "model_score": 0.0287,
  "style_score": 0.25,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "92b13568a849",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1394,
  "model_score": 0.0287,
  "style_score": 0.25,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "ec94e45ffe62",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1394,
  "model_score": 0.0287,
  "style_score": 0.25,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "fdeb3fd2d7f9",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1394,
  "model_score": 0.0287,
  "style_score": 0.25,
  "label": "We think this was probably written by a person. Nothing about it stood out to us, so there is nothing you need to do.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
