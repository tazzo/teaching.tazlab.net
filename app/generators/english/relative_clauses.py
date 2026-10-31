"""Relative Clauses (Defining & Non-defining) exercise generator.

Provides multiple-choice fill-in-the-blank questions focusing on:
- Defining vs Non-defining relative clauses (commas, essential vs extra information)
- Pronoun choice: who (people), which (things), that (defining only, never after a comma)
- Possession with 'whose' (for both people and things)
- Relative adverbs: where (places of action), when (time), why (reasons)
- Formal register and prepositions: 'to whom', 'with whom', 'in which'
- Sentential relative clauses: 'which' commenting on a whole preceding clause
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
        sentence="The girl ______ won the science competition is in my class.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="'The girl' is a person in a defining clause without commas; use 'who'.",
        clue="Antecedent is a person ('The girl') in a defining clause.",
        rule="Use 'who' for people in defining relative clauses.",
    ),
    QuestionSpec(
        sentence="This is the book ______ inspired me to become an engineer.",
        options=("which", "who", "whom", "whose"),
        correct="which",
        explanation="'The book' is a thing; use 'which' (or 'that') in a defining relative clause.",
        clue="Antecedent is a thing/object ('the book').",
        rule="Use 'which' or 'that' for things and objects in defining relative clauses.",
    ),
    QuestionSpec(
        sentence="My uncle, ______ is a pilot, flies planes all over the world.",
        options=("who", "that", "which", "whom"),
        correct="who",
        explanation="Non-defining clause between commas about a person. 'That' is NEVER used in non-defining clauses.",
        clue="Non-defining relative clause with commas about a person.",
        rule="In non-defining relative clauses (separated by commas), use 'who' for people; 'that' is forbidden.",
    ),
    QuestionSpec(
        sentence="The restaurant ______ we had dinner last night was excellent.",
        options=("where", "which", "that", "whose"),
        correct="where",
        explanation="'Where' refers to the place in which the action took place ('in the restaurant').",
        clue="Antecedent is a location where an action happens ('we had dinner').",
        rule="Use 'where' to refer to a place in which an event or activity occurs.",
    ),
    QuestionSpec(
        sentence="A mechanic is someone ______ repairs broken cars and engines.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="'Someone' refers to a person; use 'who'.",
        clue="Pronoun refers to a person ('someone').",
        rule="Use 'who' when referring to people acting as the subject of the relative clause.",
    ),
    QuestionSpec(
        sentence="The computer ______ I bought last week has already crashed twice.",
        options=("which", "who", "whose", "where"),
        correct="which",
        explanation="'The computer' is an object in a defining clause; use 'which' (or 'that').",
        clue="Antecedent is an inanimate device ('the computer').",
        rule="Use 'which' or 'that' for inanimate objects in defining relative clauses.",
    ),
    QuestionSpec(
        sentence="My grandmother, ______ is 85, walks three miles every morning.",
        options=("who", "that", "which", "whom"),
        correct="who",
        explanation="Non-defining clause (with commas) referring to a person; 'that' cannot be used.",
        clue="Non-defining clause set off by commas about a specific person.",
        rule="'That' is never used in non-defining relative clauses; use 'who' for people.",
    ),
    QuestionSpec(
        sentence="A widow is a woman ______ husband has died.",
        options=("whose", "who", "which", "whom"),
        correct="whose",
        explanation="'Whose' indicates possession ('her husband').",
        clue="Possessive relationship between 'woman' and 'husband'.",
        rule="Use 'whose' to indicate possession in both defining and non-defining clauses.",
    ),
    QuestionSpec(
        sentence="The town ______ I grew up has changed completely.",
        options=("where", "which", "that", "whose"),
        correct="where",
        explanation="'Where' refers to the location where the subject grew up.",
        clue="Location where personal history occurred ('I grew up').",
        rule="Use 'where' as a relative adverb meaning 'in which' for places.",
    ),
    QuestionSpec(
        sentence="The students ______ failed the test must take it again next Friday.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="Defining clause identifying the specific people who failed; use 'who'.",
        clue="Defining clause identifying specific people ('The students').",
        rule="'Who' defines and restricts the group of people being discussed.",
    ),
    QuestionSpec(
        sentence="Paris, ______ is known as the City of Light, attracts millions of visitors.",
        options=("which", "that", "where", "what"),
        correct="which",
        explanation="Non-defining clause (commas) about a city acting as subject of 'is'; 'that' is forbidden here.",
        clue="Non-defining clause with commas where the city is the subject of 'is'.",
        rule="In non-defining clauses about things or places acting as subjects, use 'which', never 'that'.",
    ),
    QuestionSpec(
        sentence="The boy ______ dog ran away was crying in the park.",
        options=("whose", "who", "which", "whom"),
        correct="whose",
        explanation="'Whose' indicates possession ('the boy's dog').",
        clue="Possessive link between 'boy' and 'dog'.",
        rule="Use 'whose' as the possessive relative pronoun replacing 'his/her/their'.",
    ),
    QuestionSpec(
        sentence="The phone ______ was on the kitchen table started ringing.",
        options=("which", "who", "whom", "whose"),
        correct="which",
        explanation="'The phone' is a thing; use 'which' (or 'that').",
        clue="Subject pronoun for an inanimate object ('The phone').",
        rule="Use 'which' or 'that' for things when they serve as the subject of the relative clause.",
    ),
    QuestionSpec(
        sentence="Dr. Adams, ______ examined me at the clinic, was very reassuring.",
        options=("who", "that", "which", "whose"),
        correct="who",
        explanation="Non-defining clause about a specific person; 'that' is not allowed after a comma.",
        clue="Non-defining clause about a named individual ('Dr. Adams').",
        rule="Never use 'that' in non-defining clauses with commas; always use 'who' for people.",
    ),
    QuestionSpec(
        sentence="I will never forget the day ______ we graduated from university.",
        options=("when", "where", "which", "whose"),
        correct="when",
        explanation="'When' refers to a time noun ('the day').",
        clue="Antecedent is a time expression ('the day').",
        rule="Use 'when' as a relative adverb to refer to days, times, and periods.",
    ),
    QuestionSpec(
        sentence="The umbrella ______ you lent me kept me completely dry.",
        options=("that", "who", "whose", "where"),
        correct="that",
        explanation="Defining clause specifying an object; 'that' (or 'which') is correct.",
        clue="Defining relative clause specifying a particular object.",
        rule="'That' is commonly used in defining relative clauses to refer to things.",
    ),
    QuestionSpec(
        sentence="The hotel, ______ had a rooftop swimming pool, was right by the sea.",
        options=("which", "that", "where", "what"),
        correct="which",
        explanation="Non-defining clause (between commas) describing a thing; 'that' cannot be used.",
        clue="Non-defining clause with commas with the hotel as subject of 'had'.",
        rule="Use 'which' for non-defining clauses about things; 'that' is never used between commas.",
    ),
    QuestionSpec(
        sentence="She has a friend ______ father is an ambassador.",
        options=("whose", "who", "which", "whom"),
        correct="whose",
        explanation="'Whose' expresses possession ('her friend's father').",
        clue="Possession connecting 'a friend' to 'father'.",
        rule="'Whose' shows that something belongs to or is associated with the antecedent.",
    ),
    QuestionSpec(
        sentence="The café ______ we usually have coffee is closed today.",
        options=("where", "which", "that", "whose"),
        correct="where",
        explanation="'Where' refers to the place of the activity ('at the café').",
        clue="Antecedent is a place where an activity occurs ('we have coffee').",
        rule="Use 'where' when the relative clause describes what happens inside the location.",
    ),
    QuestionSpec(
        sentence="The woman ______ lives next door is an architect.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="Defining relative clause identifying the person; use 'who'.",
        clue="Defining clause identifying which woman is being talked about.",
        rule="Use 'who' to identify people in defining relative clauses.",
    ),
)


MEDIUM_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="He arrived twenty minutes late, ______ annoyed the teacher greatly.",
        options=("which", "that", "what", "who"),
        correct="which",
        explanation="A sentential relative clause commenting on the whole previous clause uses 'which' after a comma.",
        clue="Relative clause commenting on an entire previous situation, not a single noun.",
        rule="Use 'which' in a non-defining clause to refer back to the entire previous clause or action.",
    ),
    QuestionSpec(
        sentence="The scientist to ______ the award was presented gave a moving speech.",
        options=("whom", "who", "which", "that"),
        correct="whom",
        explanation="After a preposition ('to'), the formal relative pronoun for a person is 'whom'.",
        clue="Relative pronoun directly preceded by the preposition 'to'.",
        rule="When a relative pronoun referring to a person immediately follows a preposition, use 'whom'.",
    ),
    QuestionSpec(
        sentence="Rome, ______ we spent our honeymoon, is famous for its ancient monuments.",
        options=("where", "which", "that", "whose"),
        correct="where",
        explanation="'Where' refers to the location in which the action took place ('in Rome').",
        clue="Non-defining clause describing an action performed inside the city ('we spent our honeymoon').",
        rule="Use 'where' when the clause expresses an event that occurred at or in the location.",
    ),
    QuestionSpec(
        sentence="Rome, ______ was founded in 753 BC, is the capital of Italy.",
        options=("which", "where", "that", "what"),
        correct="which",
        explanation="'Rome' is the grammatical subject of 'was founded' in a non-defining clause, not a place of action; use 'which'.",
        clue="The city is the grammatical subject of the passive verb 'was founded', not a scene of action.",
        rule="Use 'which' (not 'where') when a city or place is the subject or direct object of the relative clause.",
    ),
    QuestionSpec(
        sentence="The company, ______ headquarters are located in Zurich, announced record profits.",
        options=("whose", "which", "that", "where"),
        correct="whose",
        explanation="'Whose' expresses possession for organizations as well as people ('the company's headquarters').",
        clue="Possessive relationship between company and its headquarters.",
        rule="'Whose' can be used with companies and organizations to show possession.",
    ),
    QuestionSpec(
        sentence="She passed all her university exams with honours, ______ pleased her parents.",
        options=("which", "that", "what", "who"),
        correct="which",
        explanation="Non-defining clause referring to the entire situation in the main clause; use 'which'.",
        clue="The clause evaluates the whole preceding achievement ('passed with honours').",
        rule="A non-defining relative clause modifying a whole sentence must begin with 'which', never 'that'.",
    ),
    QuestionSpec(
        sentence="The candidate with ______ I conducted the interview seemed very capable.",
        options=("whom", "who", "which", "that"),
        correct="whom",
        explanation="Directly following the preposition 'with', the objective form 'whom' is required for people.",
        clue="Preposition 'with' directly precedes the pronoun referring to 'The candidate'.",
        rule="Prepositions placed before human relative pronouns require 'whom' (e.g. with whom, for whom).",
    ),
    QuestionSpec(
        sentence="Mount Everest, ______ peak reaches 8,848 metres, is the highest mountain on Earth.",
        options=("whose", "which", "that", "where"),
        correct="whose",
        explanation="'Whose' can be used for things and geographical features to express possession ('the peak of which').",
        clue="Possession between geographical feature and its summit ('peak').",
        rule="'Whose' can refer to inanimate objects and mountains to replace 'of which'.",
    ),
    QuestionSpec(
        sentence="The reason ______ she decided to change jobs was to have a shorter commute.",
        options=("why", "which", "where", "whose"),
        correct="why",
        explanation="'Why' is the relative adverb used after 'the reason'.",
        clue="Antecedent is the noun 'The reason'.",
        rule="Use 'why' as a relative adverb following 'the reason'.",
    ),
    QuestionSpec(
        sentence="The historic castle, ______ was constructed in the twelfth century, was damaged by fire.",
        options=("which", "that", "where", "whose"),
        correct="which",
        explanation="Non-defining clause set off by commas; 'that' cannot be used in non-defining clauses.",
        clue="Non-defining clause between commas describing the castle.",
        rule="Non-defining relative clauses for objects must use 'which'; 'that' is not permitted.",
    ),
    QuestionSpec(
        sentence="Children ______ parents are both working often attend after-school clubs.",
        options=("whose", "who", "which", "whom"),
        correct="whose",
        explanation="Defining clause indicating possession ('children whose parents').",
        clue="Possessive relationship between children and their parents.",
        rule="Use 'whose' in defining clauses to indicate familial or possessive ties.",
    ),
    QuestionSpec(
        sentence="The village in ______ my grandparents lived had no paved roads.",
        options=("which", "where", "that", "whose"),
        correct="which",
        explanation="After the preposition 'in', use 'which' ('in which' = 'where'). You cannot say 'in where'.",
        clue="Preposition 'in' precedes the pronoun referring to 'The village'.",
        rule="Use 'in which' (never 'in where' or 'in that') when a preposition governs a place noun.",
    ),
    QuestionSpec(
        sentence="The woman ______ you were talking to at the reception is the CEO.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="Defining clause referring to the person ('the woman'); 'who' is standard when the preposition is stranded at the end.",
        clue="Person referred to with stranded preposition 'to' at the end of the clause.",
        rule="In everyday English, 'who' is standard when the preposition stays at the end of the clause.",
    ),
    QuestionSpec(
        sentence="His train was cancelled due to bad weather, ______ meant he missed the conference.",
        options=("which", "that", "what", "whose"),
        correct="which",
        explanation="'Which' introduces a non-defining comment on the entire previous fact.",
        clue="Comment on the entire consequence of the cancelled train.",
        rule="Use 'which' after a comma to connect a consequence to the preceding clause.",
    ),
    QuestionSpec(
        sentence="The museum, ______ exhibits include Egyptian mummies, receives thousands of visitors.",
        options=("whose", "which", "that", "where"),
        correct="whose",
        explanation="Possession relating to the museum ('the museum's exhibits').",
        clue="Possession between institution and its collection ('exhibits').",
        rule="Use 'whose' for institutions and buildings to indicate possession of contents.",
    ),
    QuestionSpec(
        sentence="Is there any supermarket near here ______ stays open on Sundays?",
        options=("that", "where", "whose", "whom"),
        correct="that",
        explanation="In defining clauses following 'any', 'that' or 'which' is standard; 'where' cannot be the subject of 'stays'.",
        clue="Subject of the verb 'stays' following indefinite pronoun 'any supermarket'.",
        rule="Places acting as the subject of an action take 'that' or 'which', not 'where'.",
    ),
    QuestionSpec(
        sentence="The politician, ______ was accused of corruption, resigned from parliament.",
        options=("who", "that", "which", "whom"),
        correct="who",
        explanation="Subject of a non-defining clause about a person; 'that' is incorrect after a comma.",
        clue="Non-defining clause between commas with a person as grammatical subject.",
        rule="Always choose 'who' over 'that' when commas set off extra information about a person.",
    ),
    QuestionSpec(
        sentence="Venice, ______ canals are famous across the world, is threatened by rising sea levels.",
        options=("whose", "which", "that", "where"),
        correct="whose",
        explanation="Possessive relative pronoun referring to Venice ('Venice's canals').",
        clue="Possessive relationship between the city of Venice and its canals.",
        rule="'Whose' is used to show possessive attributes of geographic entities.",
    ),
    QuestionSpec(
        sentence="The person from ______ I received the parcel did not leave a name.",
        options=("whom", "who", "which", "that"),
        correct="whom",
        explanation="Preposition 'from' + relative pronoun for a person requires 'whom'.",
        clue="Preposition 'from' precedes the pronoun for 'The person'.",
        rule="Always use 'whom' directly following a preposition (from, to, with, by, of) when referring to humans.",
    ),
    QuestionSpec(
        sentence="He forgot his wife's birthday, ______ caused a big argument.",
        options=("which", "that", "what", "whose"),
        correct="which",
        explanation="Non-defining clause referring back to the whole event of forgetting the birthday.",
        clue="Relative clause commenting on the consequence of the entire preceding sentence.",
        rule="'Which' connects a consequence to the entire preceding sentence across a comma.",
    ),
)


class RelativeClausesTopic:
    id = "english.grammar.relative_clauses"
    family = "english"
    difficulties = ("easy", "medium")
    label_key = "topic.english_relative_clauses"
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


TOPIC = RelativeClausesTopic()
