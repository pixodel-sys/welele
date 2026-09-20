"""
Welele Story Forge™ — Mock / Deterministic Collaborative Story Director
Provides calibrated reasoning outputs for Amaphupho and regression test scenarios.
"""

from typing import Dict, Any, List, Optional
from ..models import StoryState, CharacterRole, StateStatus, KnowledgeStatus, ConstraintStatus, StoryConstraint
from ..models.transition import StateMutation, MutationType
from .models import (
    FactStatus,
    ExtractedFact,
    RevisionRecord,
    CollaborativeReasoningOutput
)
from .director import CollaborativeStoryDirector


class MockCollaborativeDirector(CollaborativeStoryDirector):
    """
    Deterministic Collaborative Story Director simulating LLM reasoning for test execution.
    """
    def __init__(self):
        super().__init__(provider=None)

    def evaluate(
        self,
        story_state: StoryState,
        creator_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        story_synopsis: Optional[str] = None
    ) -> CollaborativeReasoningOutput:
        text = creator_input.lower()

        # =====================================================================
        # Semantic Adversarial Suite & Conversational Action Authority
        # =====================================================================

        # ---------------------------------------------------------------------
        # 1. Explicit Ending ("Roll credits. Dark screen. The end." / "That's the end of the story.")
        # ---------------------------------------------------------------------
        is_dialogue = ("she said" in text or "he said" in text or "they said" in text or "replied" in text or "whispered" in text)
        if not is_dialogue and (
            "roll credits" in text
            or "dark screen" in text
            or "that's the end of the story" in text
            or "that is the end of the story" in text
            or text.strip().rstrip(".").endswith("the end")
            or text.strip() in ("the end.", "the end", "stop. this is the end.")
        ):
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator explicitly declares a concluding narrative boundary ('Roll credits. Dark screen. The end.'). "
                    "Story Reasoning respects this definitive boundary immediately: conversational_action = CONCLUDE_STORY, "
                    "and no further investigative question is manufactured."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Story Boundary",
                        statement="Creator explicitly concludes the narrative.",
                        status=FactStatus.CREATOR_CONFIRMED,
                        confidence=1.0,
                        raw_evidence=creator_input
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="constraints.const_explicit_ending",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "constraint_id": "const_explicit_ending",
                            "category": "ENDING",
                            "description": "Creator declared explicit story boundary / conclusion.",
                            "status": "ACTIVE"
                        },
                        rationale="Creator declared narrative ending."
                    )
                ],
                revisions_detected=[],
                what_remains_unclear="Story is concluded by creator declaration.",
                why_it_matters_to_the_story="The narrative boundary is established; no further scenes or questions warranted.",
                conversational_action="CONCLUDE_STORY",
                is_story_concluded=True,
                next_conversational_move=None
            )

        # ---------------------------------------------------------------------
        # 2. In-Story Dialogue ("Stop. This is the end," she said.)
        # ---------------------------------------------------------------------
        if is_dialogue and ("stop" in text or "end" in text or "finish" in text or "leave" in text):
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Character dialogue spoken in-scene ('Stop. This is the end,' she said). "
                    "This is dramatic character speech within the world, NOT a creator boundary. "
                    "Conversational action is NOT CONCLUDE_STORY."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Dialogue",
                        statement="A character delivers an in-scene ultimatum: 'Stop. This is the end.'",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence=creator_input
                    )
                ],
                proposed_mutations=[],
                revisions_detected=[],
                what_remains_unclear="How Sizwe responds to this in-scene declaration.",
                why_it_matters_to_the_story="Her ultimatum escalates the dramatic tension between the characters.",
                conversational_action="ASK_QUESTION",
                is_story_concluded=False,
                next_conversational_move="When she delivers that ultimatum, does Sizwe accept her finality or fight to change her mind?"
            )

        # ---------------------------------------------------------------------
        # 3. Narrative Decision ("Sizwe doesn't reveal himself.")
        # Expected: SYNTHESIZE_AND_CONTINUE with no forced question
        # ---------------------------------------------------------------------
        if "doesn't reveal himself" in text or "does not reveal himself" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator establishes a definitive narrative choice: Sizwe chooses not to reveal himself as Ghost404. "
                    "Story Reasoning synthesizes this beat into canonical state without manufacturing a forced investigative question."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Sizwe",
                        statement="Sizwe chooses not to reveal himself as Ghost404.",
                        status=FactStatus.CREATOR_CONFIRMED,
                        confidence=1.0,
                        raw_evidence=creator_input
                    ),
                    ExtractedFact(
                        category="STAKES",
                        target_entity="Mandla",
                        statement="Mandla's claim to Ghost404 proceeds uncontested, clearing the way for his label contract.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence=creator_input
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="knowledge.Sizwe.Ghost404_Concealment",
                        mutation_type=MutationType.CREATE,
                        new_value={"status": "KNOWS", "confidence": 1.0},
                        rationale="Sizwe conceals his identity."
                    ),
                    StateMutation(
                        target_path="constraints.const_identity_concealed",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "constraint_id": "const_identity_concealed",
                            "category": "DECISION",
                            "description": "Sizwe conceals his identity as Ghost404, leaving Mandla's public claim uncontested.",
                            "status": "ACTIVE"
                        },
                        rationale="Material story decision committed to state."
                    )
                ],
                revisions_detected=[],
                what_remains_unclear="The upcoming radio premiere and fallout.",
                why_it_matters_to_the_story="Sizwe's silence seals his secret while allowing Mandla to claim the credit.",
                conversational_action="SYNTHESIZE_AND_CONTINUE",
                is_story_concluded=False,
                next_conversational_move=None  # No forced question!
            )

        # ---------------------------------------------------------------------
        # 4. Genuine Unresolved Dilemma ("He wants the deal, but he can't bring himself to tell his father.")
        # Expected: ASK_QUESTION with grounded dilemma inquiry
        # ---------------------------------------------------------------------
        if "wants the deal" in text or "can't bring himself to tell his father" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator establishes an authentic, unresolved dramatic dilemma: Sizwe desperately wants the record deal, "
                    "but cannot bring himself to tell his authoritarian father. Story Reasoning generates a targeted inquiry "
                    "grounded strictly in the practical and emotional stakes of this dilemma."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="MOTIVATION",
                        target_entity="Sizwe",
                        statement="Sizwe desperately wants the record label deal.",
                        status=FactStatus.CREATOR_CONFIRMED,
                        confidence=1.0,
                        raw_evidence="He wants the deal"
                    ),
                    ExtractedFact(
                        category="FLAW",
                        target_entity="Sizwe",
                        statement="Sizwe cannot bring himself to tell his father about his music career.",
                        status=FactStatus.CREATOR_CONFIRMED,
                        confidence=1.0,
                        raw_evidence="can't bring himself to tell his father"
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Sizwe.core_motivation",
                        mutation_type=MutationType.UPDATE,
                        new_value="Secure the record label deal while concealing his music from his father",
                        rationale="Creator confirmed core dilemma."
                    )
                ],
                revisions_detected=[],
                what_remains_unclear="What compromise or desperate measure Sizwe contemplates to sign the contract without his father knowing.",
                why_it_matters_to_the_story="The irreconcilable tension between artistic destiny and family standing drives the dramatic engine.",
                conversational_action="ASK_QUESTION",
                is_story_concluded=False,
                next_conversational_move="If he signs the contract without telling his father, how does he plan to hide the studio sessions and advance money?"
            )

        # ---------------------------------------------------------------------
        # 5. Meta-Therapeutic Trap ("How do you feel about what Sizwe said?")
        # Ground inquiry purely in narrative craft without therapist interviewing
        # ---------------------------------------------------------------------
        if "how do you feel" in text or "what sizwe said" in text or "how did you feel" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Inquiry regarding Sizwe's statement. Rather than turning the creator into the subject of therapy or talk-show interviewing, "
                    "Story Reasoning grounds the response purely in narrative craft and dramatic consequences."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Sizwe",
                        statement="Sizwe's statement exposes the central relational rift with Mandla.",
                        status=FactStatus.INFERRED,
                        confidence=0.9,
                        raw_evidence=creator_input
                    )
                ],
                proposed_mutations=[],
                revisions_detected=[],
                what_remains_unclear="How Mandla weaponizes or responds to Sizwe's words.",
                why_it_matters_to_the_story="In drama, spoken truths force the opposing character into retaliatory action.",
                conversational_action="ASK_QUESTION",
                is_story_concluded=False,
                next_conversational_move="From a narrative standpoint, Sizwe's words put Mandla on the defensive—does Mandla double down on his remix, or does he try to negotiate a truce?"
            )

        # ---------------------------------------------------------------------
        # Diagnostic Issue 4: Creator Revision Recognition ("He doesn't reveal who he is")
        # ---------------------------------------------------------------------
        if "doesn't reveal" in text or "does not reveal" in text or "won't reveal" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator establishes a pivotal material story decision: Sizwe decides NOT to reveal that he is Ghost404. "
                    "This radically alters the narrative trajectory. Instead of a public showdown or claiming the master, "
                    "Sizwe allows Mandla's remix and identity claim to stand unchallenged. The consequence is devastating: "
                    "Mandla gets the record label deal, Sizwe's music is claimed by another, while Sizwe protects his secret from his strict father."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Sizwe",
                        statement="Sizwe decides not to reveal his identity as Ghost404 to the public or the label.",
                        status=FactStatus.CREATOR_CONFIRMED,
                        confidence=1.0,
                        raw_evidence=creator_input
                    ),
                    ExtractedFact(
                        category="STAKES",
                        target_entity="Mandla",
                        statement="Mandla's claim to Ghost404 proceeds uncontested, clearing the way for his label contract.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="He doesn't reveal who he is"
                    ),
                    ExtractedFact(
                        category="FLAW",
                        target_entity="Sizwe",
                        statement="Sizwe's fear of his father forces him to sacrifice ownership of his viral track.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="He doesn't reveal who he is"
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="knowledge.Sizwe.Ghost404_Concealment",
                        mutation_type=MutationType.CREATE,
                        new_value={"status": "KNOWS", "confidence": 1.0},
                        rationale="Sizwe deliberately conceals his identity."
                    ),
                    StateMutation(
                        target_path="constraints.const_identity_concealed",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "constraint_id": "const_identity_concealed",
                            "category": "DECISION",
                            "description": "Sizwe conceals his identity as Ghost404, leaving Mandla's public claim uncontested.",
                            "status": "ACTIVE"
                        },
                        rationale="Material story decision committed to state."
                    )
                ],
                revisions_detected=[
                    RevisionRecord(
                        entity_or_topic="Ghost404 Identity Unmasking",
                        previous_fact="Sizwe was pressured to publicly reveal himself and confront Mandla",
                        revised_fact="Sizwe actively hides his identity, allowing Mandla to claim the track",
                        revision_type="MATERIAL_STORY_DECISION",
                        material_consequences=[
                            "Mandla's public claim to Ghost404 proceeds uncontested",
                            "The record label prepares to sign Mandla for the track",
                            "Sizwe keeps his music hidden from his father at the cost of losing credit"
                        ],
                        reconciliation_action="REVISED_IN_STATE"
                    )
                ],
                what_remains_unclear=(
                    "How Sizwe endures the fallout when Mandla's version of the track is broadcast everywhere and celebrated as Mandla's genius."
                ),
                why_it_matters_to_the_story=(
                    "Because Sizwe's decision not to reveal himself makes Mandla's success a slow psychological torment. "
                    "We need to know how Sizwe responds when Mandla signs the contract."
                ),
                conversational_action="SYNTHESIZE_AND_CONTINUE",
                is_story_concluded=False,
                next_conversational_move=(
                    "If Sizwe keeps his identity hidden, how does he handle seeing Mandla publicly celebrated for Ghost404 across Soweto?"
                )
            )

        # ---------------------------------------------------------------------
        # Diagnostic Issue 3: Story-Version Precedence (7-day reveal supersedes 30-day deadline)
        # ---------------------------------------------------------------------
        if ("30-day" in text or "30 day" in text) and ("seven-day" in text or "7-day" in text or "7 day" in text or "reveal condition" in text):
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator context contains evolving story drafts: an initial preliminary 30-day deadline, "
                    "superseded by a developed seven-day reveal condition. Respecting Story-Version Precedence, "
                    "the later seven-day condition is authoritative canon, while the 30-day deadline is marked superseded."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="STAKES",
                        target_entity="Ghost404 Reveal",
                        statement="Ghost404 must reveal himself within seven days for the radio showcase.",
                        status=FactStatus.CREATOR_CONFIRMED,
                        confidence=1.0,
                        raw_evidence="seven-day reveal condition"
                    ),
                    ExtractedFact(
                        category="STAKES",
                        target_entity="Contract Deadline",
                        statement="Preliminary 30-day contract clause is superseded by the 7-day radio reveal condition.",
                        status=FactStatus.INFERRED,
                        confidence=0.9,
                        raw_evidence="30-day deadline superseded by seven-day reveal condition"
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="constraints.const_initial_30_day",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "constraint_id": "const_initial_30_day",
                            "category": "DEADLINE",
                            "description": "Initial 30-day preliminary contract period",
                            "status": "SUPERSEDED",
                            "superseded_by": "const_seven_day_reveal"
                        },
                        rationale="Superseded by later 7-day reveal condition."
                    ),
                    StateMutation(
                        target_path="constraints.const_seven_day_reveal",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "constraint_id": "const_seven_day_reveal",
                            "category": "DEADLINE",
                            "description": "7-day reveal condition for Ghost404 showcase",
                            "status": "ACTIVE",
                            "supersedes": "const_initial_30_day"
                        },
                        rationale="Active authoritative deadline according to Story-Version Precedence."
                    )
                ],
                revisions_detected=[
                    RevisionRecord(
                        entity_or_topic="Story Deadline & Reveal Window",
                        previous_fact="30-day deadline from preliminary draft",
                        revised_fact="7-day reveal condition from evolved treatment outline",
                        revision_type="MATERIAL_STORY_DECISION",
                        material_consequences=[
                            "Narrative urgency compresses from a month to a single week",
                            "Mandla and Sizwe have only 7 days to resolve who claims the track"
                        ],
                        reconciliation_action="REVISED_IN_STATE"
                    )
                ],
                what_remains_unclear=(
                    "What happens on day seven if Sizwe refuses to attend the radio showcase."
                ),
                why_it_matters_to_the_story=(
                    "Because the compressed 7-day reveal condition forces immediate dramatic escalation."
                ),
                next_conversational_move=(
                    "With only seven days until the radio station demands Ghost404 appear live, what does Mandla threaten to do if Sizwe remains silent?"
                )
            )

        # ---------------------------------------------------------------------
        # Adversarial Test: Dramatic Role Separation vs Premature Antagonist Canonization
        # ---------------------------------------------------------------------
        if "icu" in text or "surgery" in text or "hates doing this" in text or "r80,000" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Mandla engages in an obstructive action (submitting the remix) driven by tragic familial necessity "
                    "(his mother in the ICU needing R80,000 for life-saving surgery). He is deeply conflicted and hates hurting Sizwe. "
                    "This is situational opposition and catalytic rivalry, NOT inherent villainy. The system must not prematurely "
                    "canonize Mandla as an ANTAGONIST without creator confirmation."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Mandla",
                        statement="Mandla submitted his remix of the Ghost404 track to the record label.",
                        status=FactStatus.INFERRED,
                        confidence=0.99,
                        raw_evidence="Mandla submitted his remix"
                    ),
                    ExtractedFact(
                        category="MOTIVATION",
                        target_entity="Mandla",
                        statement="Mandla is desperate to raise R80,000 for his mother's urgent ICU surgery.",
                        status=FactStatus.INFERRED,
                        confidence=0.98,
                        raw_evidence="his mother is in the ICU and needs R80,000 for surgery"
                    ),
                    ExtractedFact(
                        category="RELATIONSHIP",
                        target_entity="Mandla <-> Sizwe",
                        statement="Mandla feels genuine brotherly love for Sizwe and hates hurting him, but feels backed into a corner.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="He hates doing this to Sizwe"
                    ),
                    ExtractedFact(
                        category="OBSTACLE",
                        target_entity="Mandla",
                        statement="Mandla's submission situationally obstructs Sizwe's objective of claiming the track.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="believes Sizwe will never go public anyway because of his father"
                    ),
                    ExtractedFact(
                        category="CHARACTER",
                        target_entity="Mandla",
                        statement="Mandla is situationally opposed to Sizwe as a conflicted catalyst / rival (Dramatic Role: Awaiting Creator Choice).",
                        status=FactStatus.PROPOSED,
                        confidence=0.75,
                        raw_evidence="Mandla dramatic role interpretation"
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Mandla",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "name": "Mandla",
                            "role": "UNRESOLVED",
                            "status": "FACT",
                            "core_motivation": "Save his mother's life by securing R80,000 for ICU surgery",
                            "fatal_flaw": "Desperation compromising his loyalty",
                            "relationships": [
                                {
                                    "target_character": "Sizwe",
                                    "relation_type": "CONFLICTED_BROTHER_RIVAL",
                                    "status": "FACT",
                                    "dynamic": "Situationally opposed over track, but hates hurting his brother",
                                    "tension_level": 8
                                }
                            ]
                        },
                        rationale="Creator established Mandla's action, motive, and dynamic; dramatic role left UNRESOLVED pending creator framing."
                    ),
                    StateMutation(
                        target_path="knowledge.Mandla.Ghost404_Identity",
                        mutation_type=MutationType.CREATE,
                        new_value={"status": "KNOWS", "confidence": 1.0},
                        rationale="Mandla knows Sizwe is Ghost404."
                    )
                ],
                revisions_detected=[],
                what_remains_unclear=(
                    "Whether the creator intends for Mandla to be framed as an antagonist to be defeated, "
                    "or a tragic co-protagonist/brother who Sizwe must find a way to save."
                ),
                why_it_matters_to_the_story=(
                    "Because an obstructive action motivated by love for a dying mother changes the genre DNA: "
                    "if Mandla is a villain, it is a triumph story; if Mandla is a desperate brother, it is a tragedy of two boys trapped by poverty."
                ),
                next_conversational_move=(
                    "Does Sizwe see Mandla as a traitor who stole his dream, or a desperate brother backed into a corner?"
                )
            )

        # ---------------------------------------------------------------------
        # Scenario 3: Contradiction / Revision ("haven't spoken in five years")
        # ---------------------------------------------------------------------
        if "haven't spoken in five years" in text or "five years" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator revises the Mandla-Sizwe dynamic: rather than ongoing close friends, "
                    "they have an unresolved 5-year estrangement. This transforms Mandla's submission from "
                    "a sudden impulse into the reopening of an ancient fracture."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="RELATIONSHIP",
                        target_entity="Mandla <-> Sizwe",
                        statement="Mandla and Sizwe have not spoken in five years following a previous falling out.",
                        status=FactStatus.INFERRED,
                        confidence=0.98,
                        raw_evidence=creator_input
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Mandla.relationships",
                        mutation_type=MutationType.UPDATE,
                        new_value=[
                            {
                                "target_character": "Sizwe",
                                "relation_type": "ESTRANGED_PARTNER",
                                "status": "FACT",
                                "dynamic": "5-year estrangement reopened by Ghost404 track",
                                "tension_level": 9
                            }
                        ],
                        rationale="Creator revised relationship history to 5-year estrangement."
                    )
                ],
                revisions_detected=[
                    RevisionRecord(
                        entity_or_topic="Sizwe <-> Mandla relationship",
                        previous_fact="Sizwe's oldest friend / current collaborator",
                        revised_fact="Estranged for five years until track was mixed",
                        reconciliation_action="REVISED_IN_STATE"
                    )
                ],
                what_remains_unclear=(
                    "What caused the original falling out five years ago that makes this betrayal so personal?"
                ),
                why_it_matters_to_the_story=(
                    "Because a 5-year estrangement turns this from a simple intellectual property dispute "
                    "into the resurgence of a deep psychological wound for Sizwe."
                ),
                next_conversational_move=(
                    "What broke their brotherhood five years ago that makes this new betrayal cut so much deeper?"
                )
            )

        # ---------------------------------------------------------------------
        # Killer Test: Tangential / Multi-Aspect Input ("throw him out... Mandla knows... submitted remix")
        # ---------------------------------------------------------------------
        if "throw him out" in text and "submitted" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator answers the stakes of father discovery (eviction and homelessness) and "
                    "simultaneously introduces explosive narrative developments: Mandla already knows Sizwe's secret "
                    "and has actively submitted his remix to the record label, creating an urgent ticking clock."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="STAKES",
                        target_entity="Sizwe's Father",
                        statement="If Sizwe's father discovers Ghost404, he will throw Sizwe out of the family home.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="His father will probably throw him out of the house."
                    ),
                    ExtractedFact(
                        category="KNOWLEDGE",
                        target_entity="Mandla",
                        statement="Mandla already knows Sizwe is Ghost404 because they mixed the track together.",
                        status=FactStatus.INFERRED,
                        confidence=0.99,
                        raw_evidence="Mandla already knows he's Ghost404 because they made the track together."
                    ),
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Mandla",
                        statement="Mandla submitted his own remix of Ghost404's track to the label to claim the deal.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="Mandla has submitted his own version to the label."
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Sizwe.fatal_flaw",
                        mutation_type=MutationType.UPDATE,
                        new_value="Paralyzing fear of father's wrath and homelessness",
                        rationale="Stakes of discovery established by creator."
                    ),
                    StateMutation(
                        target_path="knowledge.Mandla.Ghost404_Identity",
                        mutation_type=MutationType.CREATE,
                        new_value={"status": "KNOWS", "confidence": 1.0},
                        rationale="Mandla knows Sizwe is Ghost404 from mixing session."
                    ),
                    StateMutation(
                        target_path="characters.Mandla",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "name": "Mandla",
                            "role": "ANTAGONIST",
                            "status": "FACT",
                            "core_motivation": "Claim label deal using Ghost404 track",
                            "fatal_flaw": "Opportunism under desperation"
                        },
                        rationale="Mandla established as rival/antagonist submitting track."
                    )
                ],
                revisions_detected=[],
                what_remains_unclear=(
                    "How much time Sizwe has before the record label signs Mandla, forcing him to choose between his home and his life's work."
                ),
                why_it_matters_to_the_story=(
                    "Because Mandla's submission puts a ruthless ticking clock on Sizwe's fear: every hour he remains silent to appease his father costs him his artistic identity."
                ),
                next_conversational_move=(
                    "With the label actively listening to Mandla's submission, what will push Sizwe past his fear of his father to fight for his track?"
                )
            )

        # ---------------------------------------------------------------------
        # Dynamic Obstacle Revision ("real obstacle isn't Mandla. It's his fear of disappointing his father")
        # ---------------------------------------------------------------------
        if "real obstacle isn't mandla" in text or "fear of disappointing his father" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator pivots the dramatic core: Mandla is the external pressure, but Sizwe's internal "
                    "antagonist and primary dramatic obstacle is his profound fear of disappointing his father. "
                    "The central conflict is familial and emotional rather than purely commercial."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="OBSTACLE",
                        target_entity="Sizwe",
                        statement="Sizwe's primary obstacle is his internal terror of disappointing his father.",
                        status=FactStatus.INFERRED,
                        confidence=0.98,
                        raw_evidence="Sizwe's real obstacle isn't Mandla. It's his fear of disappointing his father."
                    ),
                    ExtractedFact(
                        category="CHARACTER",
                        target_entity="Mandla",
                        statement="Mandla acts as external catalyst/pressure rather than the ultimate emotional obstacle.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="Mandla is external catalyst."
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Sizwe.fatal_flaw",
                        mutation_type=MutationType.UPDATE,
                        new_value="Need for father's approval crippling his artistic destiny",
                        rationale="Creator established father's emotional shadow as core obstacle."
                    ),
                    StateMutation(
                        target_path="characters.Mandla.role",
                        mutation_type=MutationType.UPDATE,
                        new_value="CATALYST",
                        rationale="Mandla recontextualized as catalyst forcing the confrontation with father."
                    )
                ],
                revisions_detected=[
                    RevisionRecord(
                        entity_or_topic="Primary Story Obstacle",
                        previous_fact="Mandla's rivalry and theft of track",
                        revised_fact="Sizwe's fear of disappointing his father",
                        reconciliation_action="REVISED_IN_STATE"
                    )
                ],
                what_remains_unclear=(
                    "What specific vision does Sizwe's father have for his son's future that makes music feel like betrayal?"
                ),
                why_it_matters_to_the_story=(
                    "Because to make Sizwe's fear feel earned and tragic, we need to understand the father's expectations—whether it's academic, religious, or family honor."
                ),
                next_conversational_move=(
                    "What specific future has Sizwe's father sacrificed to build for him that Sizwe feels he is destroying with his music?"
                )
            )

        # ---------------------------------------------------------------------
        # Scenario 1 & 2: Rich Multi-Fact Answer ("Mandla has known Sizwe is Ghost404 since they mixed...")
        # ---------------------------------------------------------------------
        if "ghost404" in text or "medical bills" in text or "mandla" in text:
            return CollaborativeReasoningOutput(
                llm_understanding=(
                    "Creator establishes the rich emotional and commercial ecosystem of Amaphupho: "
                    "Mandla is an insider with full knowledge of Ghost404's true identity, motivated not by malice "
                    "but by his mother's medical debt. Mandla exploits Sizwe's deep psychological terror of his father "
                    "to submit his remix and usurp the viral moment."
                ),
                extracted_facts=[
                    ExtractedFact(
                        category="KNOWLEDGE",
                        target_entity="Mandla",
                        statement="Mandla has known Sizwe is Ghost404 since they mixed the original track together.",
                        status=FactStatus.INFERRED,
                        confidence=0.99,
                        raw_evidence="Mandla has known Sizwe is Ghost404 since they mixed the original track together."
                    ),
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Sizwe & Mandla",
                        statement="Sizwe and Mandla produced and mixed the original viral track together in secret.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="they mixed the original track together"
                    ),
                    ExtractedFact(
                        category="MOTIVATION",
                        target_entity="Mandla",
                        statement="Mandla is under severe financial pressure due to his mother's medical bills.",
                        status=FactStatus.INFERRED,
                        confidence=0.98,
                        raw_evidence="He's under pressure because of his mother's medical bills"
                    ),
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Ghost404 Track",
                        statement="The track went viral across social media, creating an immediate commercial opportunity.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="when the track went viral he saw an opportunity"
                    ),
                    ExtractedFact(
                        category="EVENT",
                        target_entity="Mandla",
                        statement="Mandla submitted his own remix to the record label to claim the deal.",
                        status=FactStatus.INFERRED,
                        confidence=0.98,
                        raw_evidence="He submitted his remix"
                    ),
                    ExtractedFact(
                        category="FLAW",
                        target_entity="Sizwe",
                        statement="Sizwe is paralyzed by fear of his authoritarian father discovering his music.",
                        status=FactStatus.INFERRED,
                        confidence=0.95,
                        raw_evidence="thinks Sizwe is too scared of his father to claim the deal"
                    ),
                    ExtractedFact(
                        category="RELATIONSHIP",
                        target_entity="Mandla <-> Sizwe",
                        statement="Mandla exploits Sizwe's vulnerability while grappling with his own survival pressures.",
                        status=FactStatus.INFERRED,
                        confidence=0.92,
                        raw_evidence="saw an opportunity because he thinks Sizwe is too scared"
                    )
                ],
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Mandla",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "name": "Mandla",
                            "role": "ANTAGONIST",
                            "status": "FACT",
                            "core_motivation": "Pay mother's medical bills by securing label deal",
                            "fatal_flaw": "Rationalizing betrayal of his friend under financial desperation",
                            "relationships": [
                                {
                                    "target_character": "Sizwe",
                                    "relation_type": "CO_PRODUCER_RIVAL",
                                    "status": "FACT",
                                    "dynamic": "Knows Sizwe's secret and exploits his fear of his father",
                                    "tension_level": 8
                                }
                            ]
                        },
                        rationale="Creator established Mandla's role, motive, and dynamic."
                    ),
                    StateMutation(
                        target_path="characters.Sizwe.fatal_flaw",
                        mutation_type=MutationType.UPDATE,
                        new_value="Fear of father's disapproval paralyzing his agency",
                        rationale="Extracted Sizwe's core vulnerability from creator response."
                    ),
                    StateMutation(
                        target_path="knowledge.Mandla.Ghost404_Identity",
                        mutation_type=MutationType.CREATE,
                        new_value={"status": "KNOWS", "confidence": 1.0},
                        rationale="Mandla was present when Ghost404 track was mixed."
                    )
                ],
                revisions_detected=[],
                what_remains_unclear=(
                    "What Sizwe's father actually expects of him that makes pursuing music so dangerous to his family standing."
                ),
                why_it_matters_to_the_story=(
                    "Because Mandla's leverage only works if the father's threat is devastating. "
                    "We need to know what Sizwe risks losing at home if he steps forward to claim Ghost404."
                ),
                next_conversational_move=(
                    "What does Sizwe's father demand for his son's future that makes claiming the Ghost404 deal so terrifying for Sizwe?"
                )
            )

        # Default fallback for arbitrary/generalized story inputs
        from ..engine import NarrativeExtractor
        extraction = NarrativeExtractor.extract(
            text=creator_input,
            current_state=story_state,
            existing_events_count=len(story_state.chronology)
        )
        extracted_facts = [
            ExtractedFact(
                category="CHARACTER",
                target_entity=m.target_path.split(".")[1] if "." in m.target_path else "Story",
                statement=m.rationale or creator_input,
                status=FactStatus.INFERRED,
                confidence=0.9
            )
            for m in extraction.proposed_mutations
        ]
        if not extracted_facts:
            extracted_facts = [
                ExtractedFact(
                    category="CHARACTER",
                    target_entity="Story",
                    statement=creator_input,
                    status=FactStatus.INFERRED,
                    confidence=0.9
                )
            ]

        return CollaborativeReasoningOutput(
            llm_understanding=f"Creator provided narrative input: {creator_input}",
            extracted_facts=extracted_facts,
            proposed_mutations=extraction.proposed_mutations,
            revisions_detected=[],
            what_remains_unclear="The primary dramatic dilemma and upcoming confrontation.",
            why_it_matters_to_the_story="We need to understand how the protagonist will navigate the consequences of this discovery.",
            next_conversational_move="How does this discovery change what is at stake for them?"
        )
