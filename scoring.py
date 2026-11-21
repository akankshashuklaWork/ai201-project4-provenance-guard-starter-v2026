"""
Turning two numbers into one, and one number into something a person can read.
← YOU BUILD THIS IN MILESTONES 4 AND 5

Two functions live here, and both are stubs.

`combine_signals` is where your false-positive decision from Milestone 1
actually gets made. Everything above it — the labels, the appeal path — is
downstream of a number this function produced.

`score_to_label` is where you stop writing for a machine and start writing for
a person. A score of 0.62 means nothing to a writer.

⚠️ Your README's **Signals and Scoring** section has to name the file and
function holding your combining rule. The grader checks your code against what
you claim, so that line should read `scoring.py::combine_signals`.
"""

import config


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0-1 signals into one 0-1 score.

    Both inputs point the same way: higher means more likely AI. So does the
    output.

    THE RULE (written down before it was coded):

      1. Take the weighted average of the two signals. The weights live in
         config.py (WEIGHT_MODEL_SIGNAL and WEIGHT_STYLE_SIGNAL, 0.5 each).

      2. The disagreement guard. If the two signals are more than
         config.DISAGREEMENT_GAP (0.30) apart, the result may not go above
         config.DISAGREEMENT_CAP (0.60), which is below the AI threshold.

    WHY THE GUARD: Two methods that disagree are telling us we are unsure,
    and the expensive mistake on a writing site is accusing a real writer. The
    case that made me add it: a plain human paragraph where the model signal
    said 0.86 (short ordinary sentences are very predictable) but the style
    signal said only 0.51. A plain average gave 0.68, which is "high-confidence
    AI". With the guard it becomes 0.60, "unsure". The guard only lowers
    scores, never raises them, so it only ever makes the system more cautious
    about accusing someone, and AI text can still be caught when BOTH signals
    agree.

    Args:
        model_score: from `detector.model_signal` - how predictable the text is.
        style_score: from `stylometry.style_signal` - the shape of the text.

    Returns:
        A float from 0.0 (confidently human) to 1.0 (confidently AI).
    """
    # Step 1: weighted average. Dividing by the total weight keeps the answer
    # on the 0-1 scale even if someone edits the weights so they don't add to 1.
    total_weight = config.WEIGHT_MODEL_SIGNAL + config.WEIGHT_STYLE_SIGNAL
    average = (
        config.WEIGHT_MODEL_SIGNAL * model_score
        + config.WEIGHT_STYLE_SIGNAL * style_score
    ) / total_weight

    # Step 2: if the signals split, don't let the result accuse anyone.
    if abs(model_score - style_score) > config.DISAGREEMENT_GAP:
        average = min(average, config.DISAGREEMENT_CAP)

    return min(max(average, 0.0), 1.0)


# The three label texts. They are written for someone who has never heard the
# word "threshold", and none of them states a percentage or a score.
LABEL_HUMAN = (
    "We think this was probably written by a person. "
    "Nothing about it stood out to us, so there is nothing you need to do."
)

LABEL_UNSURE = (
    "We couldn't tell whether this was written by a person or with the help of "
    "an AI tool, and we haven't made a judgement about it. Our checks can't "
    "always tell, especially with plain, simple writing, so please don't read "
    "anything into this. If you'd like someone to take a look, you can ask for "
    "a review."
)

LABEL_AI = (
    "This looks a lot like writing produced by an AI tool. Our check can be "
    "wrong, and if you wrote this yourself we would like to hear from you. "
    "You can ask for a review and a person will look at it."
)


def score_to_label(score: float) -> tuple[str, str]:
    """
    Turn a score into a guess and the text a reader actually sees.

    Returns:
        (guess, label_text) - `guess` is a short machine-readable word
        ("ai", "human" or "unsure") and `label_text` is the full sentence(s)
        shown to a person.

    Every possible score lands in exactly one of three bands (the bands are
    printed by label_ranges() below):

        score <  HUMAN_THRESHOLD              -> human
        HUMAN_THRESHOLD <= score <= AI_THRESHOLD -> unsure
        score >  AI_THRESHOLD                 -> ai

    The two edges belong to "unsure" on purpose: when a score sits exactly on a
    line, the safe answer is the one that doesn't accuse or clear anyone.
    """
    # Keep a stray out-of-range number from slipping through every band.
    score = min(max(score, 0.0), 1.0)

    if score > config.AI_THRESHOLD:
        return "ai", LABEL_AI
    if score < config.HUMAN_THRESHOLD:
        return "human", LABEL_HUMAN
    return "unsure", LABEL_UNSURE


def label_ranges() -> list[tuple[str, str]]:
    """
    The score range each label covers. Your README needs these beside the
    label text — given to you so the numbers can't drift apart from config.py.
    """
    return [
        ("high-confidence human", f"0.00 – {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"{config.HUMAN_THRESHOLD:.2f} – {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} – 1.00"),
    ]
