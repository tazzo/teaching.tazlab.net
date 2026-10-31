"""Present Perfect Simple vs Present Perfect Continuous exercise generator.

Provides multiple-choice fill-in-the-blank questions focusing on:
- Ongoing duration vs completed quantity (how long vs how many)
- Recent activity with visible present evidence vs finished result
- Stative verbs (know, believe, have, understand, own) which do not take continuous
- Time markers: already, yet, just, ever, since, for, all day, lately
"""

from __future__ import annotations

import random
from typing import NamedTuple

from app.core.verify import VerificationResult
from app.generators.base import Answer, Item, Step


class QuestionSpec(NamedTuple):
    sentence: str
    options: tuple[str, str, str, str]
    correct: str
    explanation: str
    clue: str
    rule: str


EASY_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="I ______ (know) Sarah for more than ten years.",
        options=("have known", "have been knowing", "know", "am knowing"),
        correct="have known",
        explanation="'Know' is a state verb expressing a relationship/cognition and is not used in continuous forms; use Present Perfect Simple.",
        clue="Stative verb 'know' + duration with 'for more than ten years'.",
        rule="State verbs (know, like, believe, understand) take the Present Perfect Simple, never the continuous.",
    ),
    QuestionSpec(
        sentence="She ______ (already / do) her homework, so she can relax now.",
        options=("has already done", "has already been doing", "already does", "is already doing"),
        correct="has already done",
        explanation="'Already' indicates that the action is completed before the present moment; use Present Perfect Simple.",
        clue="Adverb 'already' + present completion ('she can relax now').",
        rule="We use Present Perfect Simple with 'already' to indicate completion before expected.",
    ),
    QuestionSpec(
        sentence="He ______ (play) video games for three hours without stopping.",
        options=("has been playing", "has played", "plays", "was playing"),
        correct="has been playing",
        explanation="'For three hours without stopping' emphasizes the continuous duration of an ongoing activity.",
        clue="Continuous activity with duration marker 'for three hours without stopping'.",
        rule="We use Present Perfect Continuous to emphasize how long an action has been happening up to now.",
    ),
    QuestionSpec(
        sentence="We ______ (not see) that new film yet.",
        options=("haven't seen", "haven't been seeing", "don't see", "didn't see"),
        correct="haven't seen",
        explanation="'Yet' is used in negative sentences to show an action has not happened up to now; use Present Perfect Simple.",
        clue="Time adverb 'yet' in a negative sentence.",
        rule="Use the Present Perfect Simple with 'yet' to state that an expected event has not occurred up to the present.",
    ),
    QuestionSpec(
        sentence="It ______ (rain) all day and the garden is soaked.",
        options=("has been raining", "has rained", "rains", "is raining"),
        correct="has been raining",
        explanation="'All day' emphasizes the continuous, uninterrupted duration of the weather event.",
        clue="Duration expression 'all day' with an action verb.",
        rule="Present Perfect Continuous is used for weather and repeated actions continuing over a whole period.",
    ),
    QuestionSpec(
        sentence="How many cups of coffee ______ (you / drink) this morning?",
        options=("have you drunk", "have you been drinking", "did you drink", "do you drink"),
        correct="have you drunk",
        explanation="When asking about a completed quantity or amount ('how many cups'), use the Present Perfect Simple.",
        clue="Question with 'how many' focusing on completed quantity.",
        rule="Ask 'How many / how much' with Present Perfect Simple to focus on the result or amount produced.",
    ),
    QuestionSpec(
        sentence="They ______ (live) in Rome since 2015.",
        options=("have lived", "are living", "lived", "were living"),
        correct="have lived",
        explanation="A long-term permanent residence continuing from a past point ('since 2015') up to now takes Present Perfect Simple.",
        clue="Starting point 'since 2015' describing permanent living situation.",
        rule="Present Perfect Simple is preferred for permanent or long-standing situations continuing to the present.",
    ),
    QuestionSpec(
        sentence="I ______ (read) fifty pages of the novel so far.",
        options=("have read", "have been reading", "read", "am reading"),
        correct="have read",
        explanation="'So far' combined with a specific count ('fifty pages') requires the Present Perfect Simple.",
        clue="'So far' specifying a completed quantity ('fifty pages').",
        rule="Use Present Perfect Simple when focusing on how much of an activity is finished.",
    ),
    QuestionSpec(
        sentence="Listen! The baby ______ (cry) for twenty minutes.",
        options=("has been crying", "has cried", "cries", "is crying"),
        correct="has been crying",
        explanation="The focus is on the continuous duration ('for twenty minutes') of an action happening right up to now.",
        clue="Direct observation ('Listen!') + duration ('for twenty minutes').",
        rule="Present Perfect Continuous describes an activity continuing over time up to the present moment.",
    ),
    QuestionSpec(
        sentence="______ (you / ever / visit) London?",
        options=("Have you ever visited", "Have you ever been visiting", "Did you ever visit", "Do you ever visit"),
        correct="Have you ever visited",
        explanation="'Ever' asks about general life experience at any time up to the present moment.",
        clue="'Ever' in a question about life experience.",
        rule="Use Present Perfect Simple with 'ever' and 'never' to discuss life experiences.",
    ),
    QuestionSpec(
        sentence="He ______ (have) that bicycle since his tenth birthday.",
        options=("has had", "has been having", "has", "had"),
        correct="has had",
        explanation="'Have' in the sense of possession is a stative verb and cannot be used in continuous tenses.",
        clue="Stative verb of possession 'have' + 'since his tenth birthday'.",
        rule="State verbs of possession (have, own, belong) do not take the continuous form.",
    ),
    QuestionSpec(
        sentence="They ______ (wait) at the bus stop for forty minutes.",
        options=("have been waiting", "have waited", "are waiting", "waited"),
        correct="have been waiting",
        explanation="The activity of waiting over an extended duration ('for forty minutes') is best expressed with Present Perfect Continuous.",
        clue="Duration of an active process ('for forty minutes').",
        rule="Present Perfect Continuous highlights the ongoing duration of an action rather than its completion.",
    ),
    QuestionSpec(
        sentence="I ______ (lose) my house keys; can you help me look for them?",
        options=("have lost", "have been losing", "lost", "am losing"),
        correct="have lost",
        explanation="'Lose' is an instantaneous action with a present consequence (cannot enter the house); continuous is impossible.",
        clue="Instantaneous event with strong present relevance.",
        rule="Point-in-time actions with present results take the Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="She ______ (study) for her exam since 8 o'clock this morning.",
        options=("has been studying", "has studied", "studies", "is studying"),
        correct="has been studying",
        explanation="Emphasizes the duration of the study session starting at 8:00 and continuing into the present.",
        clue="Activity verb 'study' + starting point 'since 8 o'clock'.",
        rule="Actions continuing from a past point into the present with emphasis on effort take Present Perfect Continuous.",
    ),
    QuestionSpec(
        sentence="We ______ (buy) a new television for the living room.",
        options=("have bought", "have been buying", "are buying", "bought"),
        correct="have bought",
        explanation="The focus is on the single completed purchase and its present result in the living room.",
        clue="Completed transaction with present result.",
        rule="Use Present Perfect Simple when announcing a completed event or purchase.",
    ),
    QuestionSpec(
        sentence="Tom ______ (sleep) for ten hours — you should wake him up!",
        options=("has been sleeping", "has slept", "sleeps", "is sleeping"),
        correct="has been sleeping",
        explanation="Focus is on the uninterrupted ongoing duration ('for ten hours') continuing right now.",
        clue="Duration 'for ten hours' + advice to wake him up now.",
        rule="Present Perfect Continuous emphasizes the unbroken length of time an activity has been ongoing.",
    ),
    QuestionSpec(
        sentence="How many emails ______ (she / send) today?",
        options=("has she sent", "has she been sending", "did she send", "does she send"),
        correct="has she sent",
        explanation="'How many' asks for a completed count of items, requiring the Present Perfect Simple.",
        clue="'How many' with a plural count noun ('emails').",
        rule="Always use Present Perfect Simple when specifying or asking about the number of completed units.",
    ),
    QuestionSpec(
        sentence="I ______ (learn) English for three years and I really enjoy it.",
        options=("have been learning", "have learned", "learn", "am learning"),
        correct="have been learning",
        explanation="An ongoing learning process over a period of time ('for three years') takes Present Perfect Continuous.",
        clue="Learning process over time ('for three years').",
        rule="Present Perfect Continuous is used for ongoing skills, training, or activities developing over time.",
    ),
    QuestionSpec(
        sentence="The train ______ (just / arrive) at platform 4.",
        options=("has just arrived", "has just been arriving", "just arrived", "is just arriving"),
        correct="has just arrived",
        explanation="'Just' indicates an event completed a very short time ago (Present Perfect Simple).",
        clue="'Just' signaling very recent completion.",
        rule="Use Present Perfect Simple with 'just' for an action completed moments before speaking.",
    ),
    QuestionSpec(
        sentence="They ______ (work) in the garden all morning.",
        options=("have been working", "have worked", "work", "are working"),
        correct="have been working",
        explanation="'All morning' with an active verb highlights the duration of the physical activity.",
        clue="Duration expression 'all morning' with activity verb 'work'.",
        rule="Use Present Perfect Continuous with expressions like 'all day', 'all morning' to emphasize effort/duration.",
    ),
)


MEDIUM_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="Look at your hands, they are covered in mud! What ______ (you / do)?",
        options=("have you been doing", "have you done", "did you do", "were you doing"),
        correct="have you been doing",
        explanation="We use the Present Perfect Continuous when there is visible present evidence (mud on hands) of a recent activity.",
        clue="Visible present physical evidence ('covered in mud') of a recent activity.",
        rule="Present Perfect Continuous explains a present physical state resulting from a recent continuous action.",
    ),
    QuestionSpec(
        sentence="The kitchen walls look wonderful! I ______ (paint) them light blue.",
        options=("have painted", "have been painting", "painted", "am painting"),
        correct="have painted",
        explanation="The focus is on the completed finished result ('look wonderful'), requiring the Present Perfect Simple.",
        clue="Focus on the finished, completed result ('walls look wonderful').",
        rule="Use Present Perfect Simple when the focus is on the completed product rather than the process.",
    ),
    QuestionSpec(
        sentence="I ______ (paint) the kitchen all afternoon, which is why my shirt is stained.",
        options=("have been painting", "have painted", "painted", "was painting"),
        correct="have been painting",
        explanation="Focus is on the activity and time spent ('all afternoon') explaining a present physical consequence (stained shirt).",
        clue="Process and duration ('all afternoon') explaining a present consequence ('shirt is stained').",
        rule="Present Perfect Continuous links a prolonged activity directly to a present visual result.",
    ),
    QuestionSpec(
        sentence="Somebody ______ (eat) my chocolates — the box is half empty!",
        options=("has been eating", "has eaten", "ate", "is eating"),
        correct="has been eating",
        explanation="The action is incomplete (the box is only half empty), focusing on the ongoing or recent activity.",
        clue="Incomplete action: evidence that some chocolate remains ('box is half empty').",
        rule="Present Perfect Continuous is used when an action is unfinished or only partially completed.",
    ),
    QuestionSpec(
        sentence="The children ______ (eat) all the biscuits; there is nothing left in the jar.",
        options=("have eaten", "have been eating", "ate", "were eating"),
        correct="have eaten",
        explanation="The action is completely finished with a total result (nothing left), requiring Present Perfect Simple.",
        clue="Total completion with zero remainder ('nothing left in the jar').",
        rule="Present Perfect Simple is used when the entirety of an object has been consumed or finished.",
    ),
    QuestionSpec(
        sentence="Why are you breathing so heavily? — I ______ (run).",
        options=("have been running", "have run", "ran", "was running"),
        correct="have been running",
        explanation="Present Perfect Continuous explains a present physiological state (breathing heavily) from recent physical exertion.",
        clue="Present physical symptom ('breathing so heavily') caused by recent activity.",
        rule="We use Present Perfect Continuous to give the explanation for how someone looks, feels, or sounds now.",
    ),
    QuestionSpec(
        sentence="I ______ (write) report drafts all morning, but I ______ (only / finish) one.",
        options=("have been writing / have only finished", "have written / have only been finishing", "wrote / only finished", "am writing / only finish"),
        correct="have been writing / have only finished",
        explanation="The ongoing activity ('all morning') takes PPC, while the completed number ('only one') takes PPS.",
        clue="Contrast: duration of process ('all morning') vs completed quantity ('only one').",
        rule="Combine PPC for the duration of the process and PPS for the specific number completed.",
    ),
    QuestionSpec(
        sentence="He ______ (believe) in that theory his entire life.",
        options=("has believed", "has been believing", "believes", "is believing"),
        correct="has believed",
        explanation="'Believe' is a mental state verb and cannot be used in continuous tenses.",
        clue="Stative mental verb 'believe' + duration 'his entire life'.",
        rule="Cognitive verbs (believe, know, think that, understand) never take continuous tenses.",
    ),
    QuestionSpec(
        sentence="She is exhausted because she ______ (not sleep) well lately.",
        options=("has not been sleeping", "has not slept", "didn't sleep", "is not sleeping"),
        correct="has not been sleeping",
        explanation="'Lately' describing an ongoing or repeated condition over recent days takes Present Perfect Continuous.",
        clue="'Lately' describing a repeated or continuing state leading to exhaustion.",
        rule="Present Perfect Continuous with 'lately' or 'recently' expresses repeated or persistent habits.",
    ),
    QuestionSpec(
        sentence="We ______ (travel) through South America for the past two months.",
        options=("have been travelling", "have travelled", "are travelling", "travelled"),
        correct="have been travelling",
        explanation="'For the past two months' emphasizes an ongoing journey/activity continuing into the present.",
        clue="Extended temporary journey over 'the past two months'.",
        rule="Present Perfect Continuous describes temporary extended situations continuing now.",
    ),
    QuestionSpec(
        sentence="He ______ (break) his watch, so he doesn't know what time it is.",
        options=("has broken", "has been breaking", "broke", "was breaking"),
        correct="has broken",
        explanation="'Break' is an instantaneous action with a present result; continuous is impossible here.",
        clue="Instantaneous event with direct present consequence ('doesn't know the time').",
        rule="Actions that happen in an instant (break, lose, drop) take the Simple form.",
    ),
    QuestionSpec(
        sentence="They ______ (negotiate) the new contract for three weeks, but they haven't signed it yet.",
        options=("have been negotiating", "have negotiated", "negotiate", "are negotiating"),
        correct="have been negotiating",
        explanation="The negotiation process is still ongoing and unfinished ('haven't signed it yet').",
        clue="Unfinished collaborative process with duration 'for three weeks'.",
        rule="Use Present Perfect Continuous for extended ongoing processes that have not reached conclusion.",
    ),
    QuestionSpec(
        sentence="I ______ (call) him four times this afternoon, but his phone is switched off.",
        options=("have called", "have been calling", "called", "am calling"),
        correct="have called",
        explanation="Repeated completed events with an exact number of occurrences ('four times') take Present Perfect Simple.",
        clue="Specific number of repeated completed actions ('four times').",
        rule="When stating the exact number of times an event has occurred, use Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="She ______ (teach) at this university since she graduated.",
        options=("has been teaching", "is teaching", "taught", "was teaching"),
        correct="has been teaching",
        explanation="Active professional activity continuing from graduation to the present.",
        clue="Active career practice continuing from 'since she graduated'.",
        rule="Present Perfect Continuous highlights an active ongoing professional career or occupation.",
    ),
    QuestionSpec(
        sentence="I ______ (own) this vintage record player for over twenty years.",
        options=("have owned", "have been owning", "own", "am owning"),
        correct="have owned",
        explanation="'Own' expresses possession and is a stative verb; continuous forms are incorrect.",
        clue="Stative verb of ownership 'own' + duration 'for over twenty years'.",
        rule="Possessive verbs (own, possess, belong to) take Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="How long ______ (you / learn) Japanese?",
        options=("have you been learning", "have you learned", "do you learn", "did you learn"),
        correct="have you been learning",
        explanation="'How long' asking about an ongoing skill/learning activity takes the Present Perfect Continuous.",
        clue="Question with 'How long' about an ongoing process.",
        rule="Ask 'How long' with Present Perfect Continuous to inquire about the duration of an ongoing action.",
    ),
    QuestionSpec(
        sentence="The company ______ (develop) this new software since last year and it is almost ready.",
        options=("has been developing", "has developed", "develops", "developed"),
        correct="has been developing",
        explanation="Development in progress ('almost ready') over a timeframe starting last year.",
        clue="Unfinished work in progress ('almost ready') since last year.",
        rule="Continuous development of an ongoing project takes Present Perfect Continuous.",
    ),
    QuestionSpec(
        sentence="Scientists ______ (discover) a new species of frog in the Amazon rainforest.",
        options=("have discovered", "have been discovering", "discover", "were discovering"),
        correct="have discovered",
        explanation="A single piece of news / completed discovery takes the Present Perfect Simple.",
        clue="Announcement of a discrete completed discovery.",
        rule="Use Present Perfect Simple for announcements of recent news and one-off discoveries.",
    ),
    QuestionSpec(
        sentence="You look exhausted! ______ (you / work) on the computer all night?",
        options=("Have you been working", "Have you worked", "Did you work", "Do you work"),
        correct="Have you been working",
        explanation="Asking about the continuous activity that explains someone's present exhausted appearance.",
        clue="Present appearance ('look exhausted') attributed to activity over 'all night'.",
        rule="Present Perfect Continuous is used to question the recent activity that caused a present condition.",
    ),
    QuestionSpec(
        sentence="I ______ (never / understand) why people enjoy horror movies so much.",
        options=("have never understood", "have never been understanding", "never understood", "am never understanding"),
        correct="have never understood",
        explanation="'Understand' is a stative verb of cognition; it must take Present Perfect Simple with 'never'.",
        clue="Cognitive stative verb 'understand' + negative experience marker 'never'.",
        rule="Stative verbs of mental perception cannot be used with continuous aspect.",
    ),
)


class PresentPerfectTopic:
    id = "english.grammar.present_perfect"
    family = "english"
    difficulties = ("easy", "medium")
    label_key = "topic.english_present_perfect"
    scenarios: tuple[str, ...] = ()

    def generate(
        self,
        rng: random.Random,
        difficulty: str,
        seed: int,
        index: int,
        options: dict | None = None,
    ) -> Item:
        pool = EASY_QUESTIONS if difficulty == "easy" else MEDIUM_QUESTIONS
        perm_rng = random.Random(f"{seed}:{self.id}:{difficulty}")
        indices = list(range(len(pool)))
        perm_rng.shuffle(indices)
        chosen_spec = pool[indices[index % len(pool)]]

        # Shuffle options deterministically using rng
        shuffled_options = list(chosen_spec.options)
        rng.shuffle(shuffled_options)

        steps = (
            Step("step.grammar_analysis", f"\\text{{{chosen_spec.clue}}}"),
            Step("step.rule_application", f"\\text{{{chosen_spec.rule}}}"),
            Step("step.correct_form", f"\\textbf{{{chosen_spec.correct}}}"),
        )
        answer = Answer(
            latex=f"\\textbf{{{chosen_spec.correct}}}",
            kind="multiple_choice",
            payload={
                "options": shuffled_options,
                "correct": [chosen_spec.correct],
                "explanation": [chosen_spec.explanation],
            },
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params={},
            statement_key=chosen_spec.sentence,
            steps=steps,
            answer=answer,
        )

    def verify(self, item: Item) -> VerificationResult:
        if item.topic != self.id:
            return VerificationResult(False, "topic_mismatch")
        if item.difficulty not in self.difficulties:
            return VerificationResult(False, "invalid_difficulty")
        if item.answer.kind != "multiple_choice":
            return VerificationResult(False, "kind_mismatch")

        payload = item.answer.payload
        options = payload.get("options")
        if not options or len(options) < 3:
            return VerificationResult(False, "missing_or_insufficient_options")
        if len(set(options)) != len(options):
            return VerificationResult(False, "duplicate_options")

        correct = payload.get("correct")
        if not correct or len(correct) != 1 or correct[0] not in options:
            return VerificationResult(False, "invalid_or_missing_correct_answer")

        explanation = payload.get("explanation")
        if not explanation or not explanation[0]:
            return VerificationResult(False, "missing_explanation")

        if not item.steps or len(item.steps) < 2:
            return VerificationResult(False, "missing_steps")

        return VerificationResult(True)


TOPIC = PresentPerfectTopic()
