"""
The test texts I use to calibrate and check Provenance Guard.

Run `python calibration_run.py` to score all of them through the real signals
and print one table (both signals, the combined score and the label).

HONEST NOTE ABOUT THESE TEXTS
    They were drafted for testing, not collected from real people. The "human"
    texts are written to read the way ordinary people write (some plain, some
    messy, some formal), and the "AI" texts are written in the typical
    assistant style (even sentences, stock phrases). They are a fair first
    check but they are NOT proof. Before trusting criterion 1, swap the
    HUMAN_PLAIN list for paragraphs you actually wrote yourself.

Groups:
    AI_CLEAR        clearly AI-written
    HUMAN_CASUAL    clearly human: lumpy, specific, informal
    HUMAN_PLAIN     plain, conventional human writing. This is the group that
                    gets wrongly accused, so it is the false-positive test
    HUMAN_FORMAL    formal human writing
    AI_EDITED       AI text lightly edited by a person (typos, an added aside)
"""

AI_CLEAR = [
    "Artificial intelligence is transforming the way businesses operate in the modern world. "
    "It is important to note that organizations must carefully consider several key factors when "
    "adopting new technologies. First, companies should ensure that their data is accurate and "
    "well organized. Additionally, it is essential to provide proper training for employees. "
    "Overall, a thoughtful approach can lead to significant improvements in efficiency and productivity.",

    "Regular exercise offers numerous benefits for both physical and mental health. It helps to "
    "improve cardiovascular fitness, strengthen muscles, and boost overall energy levels. "
    "Furthermore, physical activity has been shown to reduce stress and improve mood. "
    "In conclusion, incorporating exercise into your daily routine is one of the most effective "
    "ways to maintain a healthy and balanced lifestyle.",

    "Climate change is one of the most pressing challenges facing our planet today. Rising "
    "temperatures, melting ice caps, and extreme weather events are affecting communities around "
    "the world. It is crucial that governments, businesses, and individuals work together to "
    "reduce greenhouse gas emissions. By taking meaningful action now, we can create a more "
    "sustainable future for generations to come.",

    "Effective communication is a fundamental skill in both personal and professional settings. "
    "It involves not only expressing your thoughts clearly but also listening actively to others. "
    "Moreover, understanding body language and tone can greatly enhance the quality of your "
    "interactions. Ultimately, developing strong communication skills can help build trust, "
    "resolve conflicts, and foster positive relationships.",

    "The history of the internet is a fascinating journey that spans several decades. It began as "
    "a small research project and gradually evolved into a global network connecting billions of "
    "people. Today, the internet plays a vital role in education, commerce, and entertainment. "
    "As technology continues to advance, it will undoubtedly continue to shape the way we live "
    "and work in the years ahead.",
]

HUMAN_CASUAL = [
    "Okay so my landlord finally fixed the heater, three weeks after I asked, and the guy who came "
    "left muddy boot prints across the whole hallway. I didn't even care. It was 58 degrees in "
    "there. I stood in front of the vent like an idiot for ten minutes just feeling it blow.",

    "Grandma's kitchen always smelled like cardamom and burnt toast. She never measured anything, "
    "just tossed things in, and somehow it all came out right. I tried to copy her dal last "
    "week. Total disaster. Too much salt, and the lentils were still crunchy at the center.",

    "Missed the bus again. Third time this month. Walked the whole way to school in the drizzle "
    "listening to the same four songs, and honestly? It wasn't that bad. A dog followed me for "
    "two blocks. I named him Gerald.",

    "I don't trust anyone who says they love running. I run because my knees will hate me more if "
    "I don't, and because the guy at the pharmacy looked at me kind of sadly last time. Mile two "
    "is always the worst. Mile three, you stop thinking at all, which is the actual point.",

    "The ending of that game made me so mad I closed the laptop and went outside. Eight hours! "
    "Eight hours and you give me a loading screen and a vague wink. My brother thinks it's "
    "genius. We argued about it through dinner and neither of us ate much.",
]

# The risky group. Short, common words, ordinary sentences, no flourishes.
# This is how a lot of real people (new writers, second-language writers,
# anyone writing plainly on purpose) actually write.
HUMAN_PLAIN = [
    "I went to the park with my dog on Saturday. It was a nice day and a lot of people were "
    "there. We walked around the lake two times. My dog liked playing with other dogs. "
    "Then we went home and I made lunch.",

    "My favorite season is summer. I like it because the days are long and the weather is warm. "
    "I go swimming with my friends. We also eat ice cream. School is out so I can sleep late. "
    "I wish summer was longer.",

    "I started a new job last month. The people are nice and the work is not too hard. "
    "I take the bus to get there. It takes about forty minutes. I am still learning how "
    "everything works but I think I will like it.",

    "My brother and I like to cook on Sundays. Last week we made pasta with tomato sauce. "
    "It was good but a little too salty. Next time we will use less salt. We want to try "
    "making pizza from scratch.",

    "I read a book about a boy who lives on a farm. He has a horse and two dogs. "
    "One day the horse gets lost and he goes to find it. The story is simple but I "
    "liked it. I think kids would enjoy it.",

    "The store near my house closes at nine. I went there to buy milk and bread. "
    "The line was long so I waited for a while. The cashier was friendly. "
    "I got home late and had a quick dinner.",

    "I have been learning to play the guitar. It is hard at first because my fingers hurt. "
    "I practice every day for twenty minutes. I can play three songs now. "
    "My friend says I am getting better.",

    "We had a test in math today. I studied the night before. Some of the questions were "
    "hard but I think I did okay. After school I played soccer with my friends. "
    "I was tired when I got home.",

    "My mother works at a hospital. She leaves early in the morning and comes back after dark. "
    "On her days off we go to the market together. She likes to buy fresh fruit. "
    "I am proud of her and the work she does.",

    "Last week it rained every day. I stayed inside and watched movies. "
    "My sister came over and we played cards. We made popcorn too. "
    "It was a quiet week but I had fun.",
]

HUMAN_FORMAL = [
    "The treaty, ratified in the long shadow of a war that had exhausted every party to it, "
    "satisfied almost no one: the victors resented its leniency, the vanquished its terms, and "
    "the mediators, whose reputations hung upon it, were left to defend a settlement they had "
    "privately despaired of ever seeing honoured.",

    "Whether the doctrine of precedent constrains a court, or merely counsels it, is a question "
    "that has vexed jurists since long before the modern reports; Holmes, characteristically, "
    "thought the answer lay less in logic than in the felt necessities of the time.",
]

AI_EDITED = [
    "Artifical intelligence is changing how people work and I think thats mostly good. "
    "It is important to note that companies need to think carefully about what they adopt. "
    "Honestly my team learned this the hard way. Additionally, workers should get proper "
    "training so they feel confident. Overall, a thoughtful approach can lead to real gains.",

    "Exercise has loads of benefits for body and mind, which i found out after starting last "
    "spring. It helps improve cardiovascular fitness and boost energy levels. Furthermore, "
    "it reduces stress. My sleep got better too. In short, working out is one of the best "
    "ways to stay healthy.",
]

GROUPS = {
    "AI_CLEAR": AI_CLEAR,
    "HUMAN_CASUAL": HUMAN_CASUAL,
    "HUMAN_PLAIN": HUMAN_PLAIN,
    "HUMAN_FORMAL": HUMAN_FORMAL,
    "AI_EDITED": AI_EDITED,
}
