"""
What my test runs.  UNIT 8, MILESTONE 3

`run_eval.py` reads SCENARIOS from this file and runs each one three times.
There is one scenario per acceptance criterion in `criteria.md`, and the
"criterion" number below matches the number in that file:

    1. False positives   - at most 2 in 10 human pieces labelled AI
    2. Score spread      - AI average minus human average is at least 0.30
    3. Bad input         - 6 bad requests, all refused (400/413), none a 500,
                           each one logged
    4. Label coverage    - all three labels appear, and score_to_label has no
                           gaps (0.51 and 0.95 give different labels)
    5. Appeal path       - 5 appeals all return under_review and are logged,
                           and an appeal on an unknown id is a 404

Each scenario has a "kind" that tells run_eval.py how to run it:

    "texts"   send each string to /submit with a made-up creator_id
    "bodies"  send each dict to /submit exactly as written (bad requests)
    "spread"  send an "ai" list and a "human" list and compare the averages
    "sweep"   no web request: walk every score 0.00-1.00 through score_to_label
    "appeal"  submit each text, then appeal it, then read /log to check

HONEST NOTES ABOUT WHERE THE TEXT COMES FROM
    MY_WRITING below is my own writing: short emails I sent to schools and
    companies, copied word for word, typos included. They are SHORT (15-45
    words), which is much less than the roughly 300 words the detector was
    built for, so a pass on criterion 1 partly means "too short to judge", not
    only "my writing is safe". The README says this too.

    AI_TEXTS are five paragraphs an AI assistant wrote in its usual style
    (calibration_texts.py::AI_CLEAR). They really are AI-written, which is what
    criterion 2 needs. The other calibration groups were *drafted* to read like
    different kinds of human writing; they are NOT real human writing, so they
    are used only for label coverage (criterion 4), where all that matters is
    that the service gives back every label.
"""

import calibration_texts as calib

# ── My own writing (criterion 1, and the human half of criterion 2) ──────────
# Word for word, typos kept on purpose. Greetings and sign-offs are removed.
MY_WRITING = [
    # 1. Thanking someone after an interview.
    "Thank you so much for taking time to interview me today! It was a pleasure "
    "talking to you. Our conversation has reinforced my interest in this program. "
    "I am really excited at the prospect of joining this program and look forward "
    "to hearing from you soon.",

    # 2. Asking about campus jobs. (Sounds a little formulaic, so I need to
    #    confirm I wrote it myself before I rely on it.)
    "I am writing to inquire about potential on-campus employment opportunities "
    "available to graduate students. I would appreciate any information you could "
    "provide regarding the types of positions available, the application process, "
    "and the timeline for hiring.",

    # 3. A question about a camp.
    "I am not sure how to register for Sparta camp. I dont see it anywhere in "
    "MySJSU. I hope i am not missing anything.",

    # 4. Asking about an application.
    "I applied for Data Analytics for fall 2025 in October 2024, but have not "
    "heard back from the Graduate Department yet. My admission status is still "
    "“referred to graduate department”. May I know when can i hear back "
    "for the final decision?",

    # 5. Asking when applications open.
    "Actually i am planning to apply for fall 2025. Do you know when can i can "
    "apply for fall 2025 ??",

    # 6. Asking how to register for classes.
    "Just saw the MySJSU portal. There is enrollment appointment date available. "
    "How should i register for the classes for Fall 2025?",

    # 7. A reply about my resume.
    "Thanks for sending this over. In Education section should we add upcoming "
    "courses too which I have not done yet (Generative AI, Machine Learning and "
    "Deep Learning). Rest looks good to me.",

    # 8. Checking in.
    "Wanted to check if my resume is optimised or not? When will the marketing "
    "will start?",

    # 9. A question about a job posting.
    "Is my resume being submitted for a specific open role, or is this general "
    "outreach to see if anyone's interested?",

    # 10. Asking about starting a year later.
    "I am writing this to know does Data analytics (special session) offer "
    "defferal by 1 year? I mean what if I want to start the classes next year due "
    "to some personal reasons? Hoping to hear from you soon.",
]

# Five paragraphs that really are AI-written (see the note at the top).
AI_TEXTS = list(calib.AI_CLEAR)

# For the spread test, the human side is five of my own pieces (the longest).
HUMAN_FOR_SPREAD = [MY_WRITING[i] for i in (0, 3, 5, 6, 9)]

# Ten varied inputs for label coverage: AI, human, plain, formal, edited AI.
VARIED_INPUTS = [
    calib.AI_CLEAR[0],
    calib.AI_CLEAR[1],
    MY_WRITING[0],
    MY_WRITING[2],
    calib.HUMAN_CASUAL[0],
    calib.HUMAN_PLAIN[0],
    calib.HUMAN_PLAIN[1],
    calib.HUMAN_FORMAL[0],
    calib.AI_EDITED[0],
    calib.AI_EDITED[1],
]

# Five texts for the appeal test. Each is submitted, then appealed.
APPEAL_TEXTS = [MY_WRITING[i] for i in (0, 3, 5, 6, 9)]

SCENARIOS = [
    {
        "name": "my own writing",
        "criterion": 1,
        "kind": "texts",
        "texts": MY_WRITING,
    },
    {
        "name": "score spread",
        "criterion": 2,
        "kind": "spread",
        "ai": AI_TEXTS,
        "human": HUMAN_FOR_SPREAD,
    },
    {
        "name": "bad input",
        "criterion": 3,
        "kind": "bodies",
        # check_log: after the six requests, /log must hold six new "rejected"
        # entries (one per bad request).
        "check_log": True,
        "bodies": [
            {"creator_id": "eval_bad_a"},                              # (a) no text field
            {"text": "", "creator_id": "eval_bad_b"},                  # (b) empty text
            {"text": "     ", "creator_id": "eval_bad_c"},             # (c) only spaces
            {"text": 12345, "creator_id": "eval_bad_d"},               # (d) a number
            {"text": "Real writing here."},                            # (e) no creator_id
            {"text": "word " * 10000, "creator_id": "eval_bad_f"},     # (f) 50,000 characters
        ],
    },
    {
        "name": "label coverage",
        "criterion": 4,
        "kind": "texts",
        "texts": VARIED_INPUTS,
    },
    {
        "name": "score to label sweep",
        "criterion": 4,
        "kind": "sweep",
    },
    {
        "name": "appeal path",
        "criterion": 5,
        "kind": "appeal",
        "texts": APPEAL_TEXTS,
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.
    """
    problems = []
    kinds = {"texts", "bodies", "spread", "sweep", "appeal"}

    for i, scenario in enumerate(SCENARIOS, 1):
        name = scenario.get("name")
        kind = scenario.get("kind", "texts")
        if not name:
            problems.append(f"scenario {i} has no name")
        if kind not in kinds:
            problems.append(f"scenario {i} ('{name}') has an unknown kind '{kind}'")
            continue

        if kind == "sweep":
            continue  # nothing to send

        if kind == "bodies":
            bodies = scenario.get("bodies")
            if not bodies:
                problems.append(f"scenario {i} ('{name}') has no bodies")
                continue
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(f"scenario {i}, body {j} is not a dict")
            continue

        if kind == "spread":
            for side in ("ai", "human"):
                if not scenario.get(side):
                    problems.append(f"scenario {i} ('{name}') has no '{side}' texts")
            texts = list(scenario.get("ai", [])) + list(scenario.get("human", []))
        else:
            texts = scenario.get("texts")
            if not texts:
                problems.append(f"scenario {i} ('{name}') has no texts")
                continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(f"scenario {i} ('{name}'), text {j} is empty")
            elif str(text).startswith("REPLACE ME"):
                problems.append(f"scenario {i} ('{name}'), text {j} is still the placeholder")
    return problems
