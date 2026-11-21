"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── Settings for the style signal ────────────────────────────────────────────
# Each measure is turned into a 0-1 "AI-ness" score (1 = looks like AI) by
# stretching it between two anchor values. The anchors came from looking at my
# own 24 calibration texts (see calibration_texts.py), so they are a first guess
# and unit 8's attacks are expected to find where they are wrong.

# Sentence-length spread (coefficient of variation = stdev / mean).
# At or above SPREAD_HUMAN the sentences vary a lot -> scores 0 (human-like).
# At or below SPREAD_AI the sentences march in step -> scores 1 (AI-like).
SPREAD_HUMAN = 0.60
SPREAD_AI = 0.10

# Punctuation density (marks other than full stops, per word).
# At or above PUNCT_AI the text is comma-heavy ("Furthermore, ... Additionally,")
# -> scores 1. Zero punctuation beyond full stops -> scores 0.
PUNCT_AI = 0.07

# Type-token ratio, measured on the first TTR_WINDOW words only so a long text
# and a short one can be compared. At or above TTR_HUMAN -> 0, at or below
# TTR_AI -> 1.
TTR_WINDOW = 100
TTR_HUMAN = 0.95
TTR_AI = 0.60

# How much each measure counts inside the style signal. Spread gets the most
# because it separated my calibration texts best. Type-token ratio gets the
# least: on short texts it did not separate human from AI at all, so it is here
# for completeness but must not decide anything.
W_SPREAD = 0.50
W_PUNCT = 0.35
W_TTR = 0.15


def _stretch(value: float, zero_at: float, one_at: float) -> float:
    """
    Map `value` onto 0-1, where `zero_at` gives 0 and `one_at` gives 1.
    Works in either direction (zero_at may be bigger than one_at) and clamps
    anything outside the anchors, so one extreme text cannot break the scale.
    """
    fraction = (value - zero_at) / (one_at - zero_at)
    return min(max(fraction, 0.0), 1.0)


# ── The three measures ───────────────────────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies.

    Returns the coefficient of variation: the standard deviation of sentence
    lengths (in words) divided by their mean. Dividing by the mean means a long
    text and a short one are comparable.

    Scale: 0.0 means every sentence is the same length; around 0.6 or more
    means lumpy, human-like writing. **Higher = more human.**

    Edge case: with fewer than two sentences there is no spread to measure, so
    this returns 0.0 -- but style_signal() checks for that case separately and
    treats it as "no information" rather than "robotic".
    """
    lengths = [len(words(sentence)) for sentence in sentences(text)]
    lengths = [n for n in lengths if n > 0]      # ignore "sentences" with no words

    if len(lengths) < 2:
        return 0.0

    average = statistics.mean(lengths)
    return statistics.stdev(lengths) / average


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words, on the first TTR_WINDOW words.

    Scale: 0 to 1. **Higher = more varied vocabulary = more human.**

    Only the first 100 words count, because this ratio naturally falls as text
    gets longer (common words keep repeating). Cutting every text to the same
    length stops a long text looking "repetitive" just for being long.
    """
    all_words = words(text)[:TTR_WINDOW]
    if not all_words:
        return 0.0
    return len(set(all_words)) / len(all_words)


def punctuation_density(text: str) -> float:
    """
    Punctuation marks per word, not counting full stops and apostrophes.

    Counted: commas, semicolons, colons, dashes, brackets, question marks,
    exclamation marks. Full stops are left out because every text has about one
    per sentence, which tells us nothing. Apostrophes are left out because they
    are mostly contractions, not style.

    Scale: 0 upward. 0 means a text of plain full-stop sentences. The generated
    prose in my calibration set sat around 0.05-0.08 (lots of "Furthermore,"
    and list commas), while plain human writing was close to 0.
    """
    all_words = words(text)
    if not all_words:
        return 0.0
    marks = re.findall(r"[,;:!?()\u2014\u2013-]", text)
    return len(marks) / len(all_words)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0-1 score. **Higher means more likely AI.**

    How each measure points, and how it is flipped so they all agree:

        sentence_length_spread   high = human, so we FLIP it (low spread -> AI)
        type_token_ratio         high = human, so we FLIP it (low ratio -> AI)
        punctuation_density      high = AI-like in my data, so it is NOT flipped

    Each is stretched onto 0-1 first (so a raw ratio and a raw count can be
    added fairly), then they are blended with the W_* weights above.

    If the text has no words at all (for example "!!! ???") or only one
    sentence, there is little or nothing to measure, so that part falls back to
    0.5, meaning "no opinion", instead of guessing.
    """
    all_words = words(text)
    if not all_words:
        return 0.5

    # Spread needs at least two sentences, or it says nothing.
    if len(sentences(text)) < 2:
        spread_score = 0.5
    else:
        spread_score = _stretch(sentence_length_spread(text), SPREAD_HUMAN, SPREAD_AI)

    punct_score = _stretch(punctuation_density(text), 0.0, PUNCT_AI)
    ttr_score = _stretch(type_token_ratio(text), TTR_HUMAN, TTR_AI)

    score = W_SPREAD * spread_score + W_PUNCT * punct_score + W_TTR * ttr_score
    return round(min(max(score, 0.0), 1.0), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
