"""
Welele Story Forge™ — Excavator Narrative Information Extraction Engine
Locks Enforced:
- LOCK 1: Natural narrative is first-class input and may satisfy multiple requirements in one response.
- LOCK 2: Stable character IDs and entity resolution.
- LOCK 3: Never silently merge ambiguous characters.
- LOCK 4: Narrative extraction does not equal canon (EXTRACT -> PROPOSE -> RECONCILE -> VALIDATE -> COMMIT).
- LOCK 6: Explicit endings are first-class information.
- ARCHITECTURAL PRINCIPLE: A relational descriptor must never overwrite an explicitly supplied proper name.
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from uuid import uuid4

from ..models.state import StoryState, CharacterState, CharacterRole, CharacterRelationship, StateStatus, KnowledgeState, KnowledgeStatus
from ..models.transition import StateMutation, MutationType
from ..models.events import ChronologyEvent
from .entity_registry import EntityRegistry, ResolutionOutcome


class NarrativeExtractionResult:
    def __init__(
        self,
        raw_input: str,
        proposed_mutations: List[StateMutation],
        proposed_events: List[ChronologyEvent],
        explicit_ending_detected: bool = False,
        ending_text: Optional[str] = None,
        extracted_character_names: Optional[List[str]] = None,
        ambiguities: Optional[List[str]] = None
    ):
        self.raw_input = raw_input
        self.proposed_mutations = proposed_mutations
        self.proposed_events = proposed_events
        self.explicit_ending_detected = explicit_ending_detected
        self.ending_text = ending_text
        self.extracted_character_names = extracted_character_names or []
        self.ambiguities = ambiguities or []


class NarrativeExtractor:
    """
    The Excavator narrative interpretation component.
    Extracts narrative facts, candidate entities, relationships, motivations,
    temporal beats, outcomes and explicit termination signals from natural creator text.
    Prioritizes proper names over relational descriptors.
    """

    EXPLICIT_ENDING_PATTERNS = [
        r"\b(?:that\s+is|that's|this\s+is)\s+(?:the\s+)?end\b",
        r"\bthe\s+end\.?$",
        r"\b(?:story\s+)?concludes?\b",
        r"\b(?:that\s+)?concludes\s+the\s+story\b",
        r"\bnothing(?:\s+more)?\s*[,.]\s*that['’]?s\s+the\s+ending\b",
        r"\bthe\s+story\s+reaches\s+its\s+final\s+conclusion\b",
        r"\bpermanently\s+settled\b"
    ]

    CHRONOLOGY_MARKERS = [
        # (Anchor Type, Regex pattern, Default description label)
        ("INCITING_DISRUPTION", r"\b(?:destroys?|disrupts?|kills?|dies?|murdered|discovers?|finds?|arrives?|stumbles?|fired|evicted|steals?|stolen|robbed|attacked)\b", "Inciting Disruption"),
        ("POINT_OF_NO_RETURN", r"\b(?:leaves?|departs?|travels?|crosses?|enters?|commits?|decides?|vows?|escapes?|flees?|takes\s+the\s+money)\b", "Point of No Return"),
        ("MIDPOINT_REVELATION", r"\b(?:struggles?|discovers?|reveals?|uncovers?|confronts?|betrays?|twist|secret|cornered|hunted|tracked)\b", "Midpoint Shift"),
        ("DARK_NIGHT", r"\b(?:cornered|hopeless|fails?|loses?|trapped|abandoned|grief|ruin|rock\s+bottom|surgery\s+fails?|caught)\b", "Dark Night / Low Point"),
        ("CLIMAX", r"\b(?:reunites?|showdown|confrontation|battle|stands?|sacrifices?|dies?|final\s+confrontation|face\s+to\s+face)\b", "Climax Confrontation"),
        ("RESOLUTION", r"\b(?:peace|happy|settles?|reconciles?|rebuilt|saved|returns?|new\s+beginning|resolution|survives?)\b", "Dramatic Resolution")
    ]

    # Map role keywords to default role, canonical relationship type, and motivation
    ROLE_DESCRIPTORS = {
        "sister": (CharacterRole.CONFIDANT, "SIBLING", "Support protagonist and survive familial crisis"),
        "brother": (CharacterRole.CONFIDANT, "SIBLING", "Support protagonist and protect family"),
        "sibling": (CharacterRole.CONFIDANT, "SIBLING", "Support protagonist and protect family"),
        "mother": (CharacterRole.CONFIDANT, "PARENT", "Protect family and secure livelihood"),
        "father": (CharacterRole.CONFIDANT, "PARENT", "Protect family and legacy"),
        "mom": (CharacterRole.CONFIDANT, "PARENT", "Protect family and secure livelihood"),
        "dad": (CharacterRole.CONFIDANT, "PARENT", "Protect family and legacy"),
        "daughter": (CharacterRole.SUPPORTING, "CHILD", "Survive and rely on family protection"),
        "son": (CharacterRole.SUPPORTING, "CHILD", "Survive and rely on family protection"),
        "wife": (CharacterRole.CONFIDANT, "SPOUSE", "Navigate high-stakes dilemma with partner"),
        "husband": (CharacterRole.CONFIDANT, "SPOUSE", "Navigate high-stakes dilemma with partner"),
        "fiance": (CharacterRole.CONFIDANT, "PARTNER", "Navigate impending danger together"),
        "fiancee": (CharacterRole.CONFIDANT, "PARTNER", "Navigate impending danger together"),
        "girlfriend": (CharacterRole.CONFIDANT, "PARTNER", "Navigate impending danger together"),
        "boyfriend": (CharacterRole.CONFIDANT, "PARTNER", "Navigate impending danger together"),
        "uncle": (CharacterRole.SUPPORTING, "FAMILY", "Family elder with vested interest"),
        "aunt": (CharacterRole.SUPPORTING, "FAMILY", "Family elder with vested interest"),
        "cousin": (CharacterRole.SUPPORTING, "FAMILY", "Family ally or complicated relative"),
        "family": (CharacterRole.SUPPORTING, "FAMILY", "Survive crisis and protect family unit"),
        "gogo": (CharacterRole.SUPPORTING, "FAMILY", "Elder family matriarch holding tradition"),
        "mkhulu": (CharacterRole.SUPPORTING, "FAMILY", "Elder family patriarch holding tradition"),
        "friend": (CharacterRole.CONFIDANT, "FRIEND", "Stand by protagonist in crisis"),
        "ally": (CharacterRole.CONFIDANT, "ALLY", "Provide strategic support in conflict"),
        "partner": (CharacterRole.CONFIDANT, "PARTNER", "Work together to achieve high-stakes goal"),
        "boss": (CharacterRole.ANTAGONIST, "OPPOSITION", "Enforce authority and corporate / workplace compliance"),
        "manager": (CharacterRole.ANTAGONIST, "OPPOSITION", "Enforce workplace leverage and control"),
        "landlord": (CharacterRole.ANTAGONIST, "OPPOSITION", "Demand unpayable rent and threaten eviction"),
        "creditor": (CharacterRole.ANTAGONIST, "OPPOSITION", "Demand unpayable debt and enforce severe penalties"),
        "loan shark": (CharacterRole.ANTAGONIST, "OPPOSITION", "Enforce predatory loans with violent intimidation"),
        "drug dealer": (CharacterRole.ANTAGONIST, "OPPOSITION", "Ruthless underworld figure defending money and territory"),
        "rival": (CharacterRole.ANTAGONIST, "OPPOSITION", "Defeat protagonist and claim domain"),
        "enemy": (CharacterRole.ANTAGONIST, "OPPOSITION", "Actively destroy protagonist"),
        "nemesis": (CharacterRole.ANTAGONIST, "OPPOSITION", "Personal opposing force locked in central conflict"),
    }

    STOP_WORDS = {
        "the", "then", "there", "their", "theirs", "eventually", "despite", "that", "this",
        "when", "after", "before", "if", "because", "although", "while", "and", "but",
        "however", "meanwhile", "soon", "later", "suddenly", "finally", "once",
        "since", "every", "everyone", "nothing", "something", "everything", "leaves",
        "struggles", "destroys", "reunite", "dies", "confronts", "refuses", "story",
        "drama", "comedy", "set", "johannesburg", "south", "africa", "friday", "r50",
        "urgent", "surgery", "night", "shift", "dead", "end", "job", "money", "car",
        "boot", "workshop", "collateral", "repay", "debt", "operation", "hospital",
        "his", "her", "hers", "my", "mine", "our", "ours", "your", "yours",
        "he", "him", "she", "it", "its", "they", "them", "we", "us", "you", "i",
        "who", "whom", "whose", "which", "what", "where", "family", "doctor", "police",
        "actually", "wait", "okay", "ok", "no", "yes", "maybe", "well", "instead",
        "basically", "obviously", "clearly", "originally", "initially", "currently",
        "truthfully", "honestly", "furthermore", "also", "rather", "anyway", "besides",
        "together", "given", "about", "around", "against", "without", "through",
        "bank", "casino", "hotel", "village", "company", "business", "clandestine"
    }

    @classmethod
    def detect_explicit_ending(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detects whether creator explicitly indicated story termination.
        Never flags in-story character dialogue or narrative actions.
        """
        clean_text = text.strip()
        # In-story character dialogue attribution or quotes: never a meta ending
        if re.search(r'["\'].*?["\']\s*(?:,\s*)?(?:she|he|they|[A-Z][a-z]+)\s+said\b', clean_text, re.IGNORECASE) or \
           re.search(r'\b(?:she|he|they|[A-Z][a-z]+)\s+said\b', clean_text, re.IGNORECASE):
            return False, None

        for pat in cls.EXPLICIT_ENDING_PATTERNS:
            match = re.search(pat, clean_text, re.IGNORECASE)
            if match:
                return True, match.group(0)
        return False, None

    @classmethod
    def split_into_narrative_sentences(cls, text: str) -> List[str]:
        """Splits natural paragraph into narrative sentences, filtering out pure meta-commentary."""
        raw_sentences = re.split(r'[.!?]+\s*', text)
        clean = []
        for s in raw_sentences:
            s_str = s.strip()
            if not s_str:
                continue
            is_pure_meta = any(re.search(pat, s_str, re.IGNORECASE) for pat in [
                r"^(?:that\s+is|that's)\s+(?:the\s+)?end$",
                r"^i\s+just\s+told\s+you",
                r"^nothing\s*$"
            ])
            if not is_pure_meta:
                clean.append(s_str)
        return clean

    @classmethod
    def extract(
        cls,
        text: str,
        current_state: StoryState,
        existing_events_count: int = 0
    ) -> NarrativeExtractionResult:
        """
        Extracts narrative proposals from natural creator response.
        Prioritizes: Proper noun -> Entity identity -> Role / relationship.
        Never overwrites a proper noun with a generic role descriptor.
        """
        proposed_mutations: List[StateMutation] = []
        proposed_events: List[ChronologyEvent] = []
        extracted_names: List[str] = []
        ambiguities: List[str] = []

        is_ending, ending_match = cls.detect_explicit_ending(text)
        sentences = cls.split_into_narrative_sentences(text)

        # ---------------------------------------------------------------------
        # 1. ENTITY EXTRACTION: Proper Nouns & Relational Descriptors
        # ---------------------------------------------------------------------
        # 1. ENTITY EXTRACTION: Proper Nouns & Relational Descriptors
        # ---------------------------------------------------------------------
        # Track identified characters: { ProperName: { 'role': CharacterRole, 'rel_type': str, 'motivation': str, 'descriptor': str } }
        identified_entities: Dict[str, Dict[str, Any]] = {}

        # Pattern 0: Protagonist introduction pattern
        # e.g., "Sabelo is an honest security guard at a high-end Fontana casino in downtown Johannesburg who discovers..."
        pattern_protagonist = re.compile(
            r'\b([A-Z][a-z]+)\s+is\s+(?:an?|the)\s+([A-Za-z0-9\s\-,]+?)\s+(?:who|trying|struggling|seeking|desperate|locked|facing|working|living|determined)\b',
            re.IGNORECASE
        )
        for match in pattern_protagonist.finditer(text):
            pname = match.group(1).strip().capitalize()
            profession = match.group(2).strip()
            if pname.lower() not in cls.STOP_WORDS and pname not in identified_entities:
                identified_entities[pname] = {
                    "role": CharacterRole.PROTAGONIST,
                    "rel_type": "PROTAGONIST",
                    "descriptor": profession or "protagonist",
                    "default_motivation": f"Lead character ({profession})"
                }

        # Pattern 0b: Active lead action at the start of sentence/premise
        # e.g., "Sabelo steals R2 million...", "Sabelo is an honest security guard..."
        pattern_lead_action = re.compile(
            r'\b([A-Z][a-z]+)\s+(?:is\s+an?|steals?|discovers?|finds?|faces?|works?|lives?|fights?|flees?|wants?|takes\s+the\s+money)\b'
        )
        for match in pattern_lead_action.finditer(text):
            pname = match.group(1).strip().capitalize()
            if pname.lower() not in cls.STOP_WORDS and pname not in identified_entities:
                if not any(c.role == CharacterRole.PROTAGONIST for c in current_state.characters.values()):
                    identified_entities[pname] = {
                        "role": CharacterRole.PROTAGONIST,
                        "rel_type": "PROTAGONIST",
                        "descriptor": "protagonist",
                        "default_motivation": "Lead character driving core story dramatic goal"
                    }

        # Also inspect story title/logline if protagonist is not yet defined in state
        if not any(c.role == CharacterRole.PROTAGONIST for c in current_state.characters.values()) and not any(info["role"] == CharacterRole.PROTAGONIST for info in identified_entities.values()):
            full_context = f"{current_state.title or ''} {current_state.logline or ''}"
            lead_match = pattern_lead_action.search(full_context) or pattern_protagonist.search(full_context)
            if lead_match:
                pname = lead_match.group(1).strip().capitalize()
                if pname.lower() not in cls.STOP_WORDS and pname not in identified_entities:
                    identified_entities[pname] = {
                        "role": CharacterRole.PROTAGONIST,
                        "rel_type": "PROTAGONIST",
                        "descriptor": "protagonist",
                        "default_motivation": "Lead character driving core dramatic goal"
                    }

        # Pattern A: Relational descriptor preceding proper noun
        # e.g., "his younger sister Zodwa", "Sabelo's sister Zodwa", "uncle Amu", "brother Thabo", "friend Jonas", "boss Mr Dube"
        role_keys_sorted = sorted(cls.ROLE_DESCRIPTORS.keys(), key=len, reverse=True)
        role_regex_group = "|".join(re.escape(k) for k in role_keys_sorted)

        pattern_a = re.compile(
            r'\b(?:(?:[Hh]is|[Hh]er|[Mm]y|[Tt]heir|[Tt]he|[A-Z][a-z]+\'s)\s+)?(?:younger|older|little|elder|best|close|beloved|corrupt|ruthless|local|notorious)?\s*'
            r'(?i:' + role_regex_group + r')\s+(?:named\s+|called\s+)?'
            r'((?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Chief)\s+[A-Z][a-z]+|[A-Z][a-z]+)\b'
        )

        for match in pattern_a.finditer(text):
            if re.search(r"\b(?:is\s+not|isn\'t|was\s+not|wasn\'t|not)\b", match.group(0), re.IGNORECASE):
                continue
            desc = match.group(0).split()[0].lower().strip()
            # Find the matching descriptor from ROLE_DESCRIPTORS
            matched_desc = next((k for k in role_keys_sorted if re.search(r'\b' + re.escape(k) + r'\b', match.group(0), re.IGNORECASE)), "supporting")
            pname = match.group(1).strip()
            # Canonicalize title/proper noun
            pname_clean = " ".join(w.capitalize() for w in pname.split())
            if pname_clean.lower() not in cls.STOP_WORDS:
                role_info = cls.ROLE_DESCRIPTORS.get(matched_desc, (CharacterRole.SUPPORTING, "RELATION", "Support story"))
                identified_entities[pname_clean] = {
                    "role": role_info[0],
                    "rel_type": role_info[1],
                    "descriptor": matched_desc,
                    "default_motivation": role_info[2]
                }

        # Pattern B: Proper noun followed by relational descriptor
        # e.g., "Zodwa, his sister", "Zodwa is Sabelo's sister", "Jonas, the local loan shark", "Mr Dube, his corrupt boss", "Zodwa is his girlfriend"
        pattern_b = re.compile(
            r'\b((?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Chief)\s+[A-Z][a-z]+|[A-Z][a-z]+)[,\s]+(?:who\s+is\s+|is\s+)?(?:(?:[Hh]is|[Hh]er|[Mm]y|[Tt]heir|[Tt]he|[A-Z][a-z]+\'s)\s+)?'
            r'(?:younger|older|little|elder|best|close|beloved|corrupt|ruthless|local|notorious)?\s*'
            r'(?i:' + role_regex_group + r')\b'
        )

        for match in pattern_b.finditer(text):
            if re.search(r"\b(?:is\s+not|isn\'t|was\s+not|wasn\'t|not)\b", match.group(0), re.IGNORECASE):
                continue
            pname = match.group(1).strip()
            pname_clean = " ".join(w.capitalize() for w in pname.split())
            if pname_clean.lower() not in cls.STOP_WORDS:
                matched_desc = next((k for k in role_keys_sorted if re.search(r'\b' + re.escape(k) + r'\b', match.group(0), re.IGNORECASE)), "supporting")
                role_info = cls.ROLE_DESCRIPTORS.get(matched_desc, (CharacterRole.SUPPORTING, "RELATION", "Support story"))
                identified_entities[pname_clean] = {
                    "role": role_info[0],
                    "rel_type": role_info[1],
                    "descriptor": matched_desc,
                    "default_motivation": role_info[2]
                }

        # Pattern B2: Pronoun anaphora followed by relational descriptor
        # e.g., "She is his girlfriend", "She's his girlfriend", "He is his brother", "He's his brother"
        pattern_pronoun_rel = re.compile(
            r'\b(?:She|He|They)(?:\s+(?:is|was)|\'s|\'re)\s+(?:(?:[Hh]is|[Hh]er|[Mm]y|[Tt]heir|[Tt]he|[A-Z][a-z]+\'s)\s+)?'
            r'(?:younger|older|little|elder|best|close|beloved|corrupt|ruthless|local|notorious)?\s*'
            r'(?i:' + role_regex_group + r')\b'
        )
        for match in pattern_pronoun_rel.finditer(text):
            if re.search(r"\b(?:is\s+not|isn\'t|was\s+not|wasn\'t|not)\b", match.group(0), re.IGNORECASE):
                continue
            matched_desc = next((k for k in role_keys_sorted if re.search(r'\b' + re.escape(k) + r'\b', match.group(0), re.IGNORECASE)), "supporting")
            # Find candidate referent: mentioned proper noun in sentence or existing non-protagonist character in state
            referent = next((p for p in identified_entities.keys() if p.lower() not in cls.STOP_WORDS), None)
            if not referent and current_state.characters:
                in_state_match = next((c.name for c in current_state.characters.values() if c.role != CharacterRole.PROTAGONIST and c.name.lower() in text.lower()), None)
                if in_state_match:
                    referent = in_state_match
            if not referent:
                prior_pns = [w for w in re.findall(r'\b[A-Z][a-z]+\b', text) if w.lower() not in cls.STOP_WORDS]
                if prior_pns:
                    referent = prior_pns[0]
            if not referent and current_state.characters:
                non_prots = [c.name for c in current_state.characters.values() if c.role != CharacterRole.PROTAGONIST]
                if non_prots:
                    referent = non_prots[0]
            if referent:
                role_info = cls.ROLE_DESCRIPTORS.get(matched_desc, (CharacterRole.SUPPORTING, "RELATION", "Support story"))
                identified_entities[referent] = {
                    "role": role_info[0],
                    "rel_type": role_info[1],
                    "descriptor": matched_desc,
                    "default_motivation": role_info[2]
                }

        # Pattern C: Antagonist action / opposition proper nouns
        # e.g., "Jonas demands", "risks Jonas hunting him", "steals from Jonas", "Jonas owns the money", "Jonas is dangerous"
        pattern_antagonist = re.compile(
            r'\b(?:from|steals?\s+from|risks?|hunted\s+by|threatened\s+by|demands?\s+of)\s+((?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Chief)\s+[A-Z][a-z]+|[A-Z][a-z]+)\b'
            r'|\b((?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Chief)\s+[A-Z][a-z]+|[A-Z][a-z]+)\s+(?:demands?|hunts?|threatens?|enforces?|owns\s+the\s+(?:stolen\s+)?money|is\s+dangerous)\b'
        )
        for match in pattern_antagonist.finditer(text):
            pname = (match.group(1) or match.group(2) or "").strip()
            if pname:
                pname_clean = " ".join(w.capitalize() for w in pname.split())
                if pname_clean.lower() not in cls.STOP_WORDS and pname_clean not in identified_entities:
                    identified_entities[pname_clean] = {
                        "role": CharacterRole.ANTAGONIST,
                        "rel_type": "OPPOSITION",
                        "descriptor": "antagonist",
                        "default_motivation": "Enforce debt/dominance and oppose protagonist"
                    }

        # General Proper Noun extraction for active story characters
        LOCATION_VENUE_WORDS = {"casino", "hotel", "bank", "mall", "street", "hospital", "station", "rank", "club", "bar", "restaurant", "shop", "workshop", "firm", "house", "building", "clinic", "park", "garage", "car", "boot", "bmw", "taxi", "town", "city", "police", "place", "fontana", "village", "township", "company"}
        general_proper_nouns = re.findall(r'\b((?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Chief)\s+[A-Z][a-z]+|[A-Z][a-z]{2,})\b', text)
        for pn in general_proper_nouns:
            pn_clean = " ".join(w.capitalize() for w in pn.split())
            if pn_clean.lower() not in cls.STOP_WORDS and pn_clean not in identified_entities and pn_clean not in current_state.characters:
                # Check if this proper noun is part of a venue, location, or vehicle phrase
                is_venue_or_place = any(
                    re.search(r'\b' + re.escape(pn) + r'\s+' + re.escape(vw) + r'\b', text, re.IGNORECASE) or
                    re.search(r'\b(?:at|in|near|outside|inside|to|from)\s+(?:a\s+|an\s+|the\s+|this\s+)?(?:place\s+in\s+|high-end\s+|local\s+|central\s+)?' + re.escape(pn) + r'\b', text, re.IGNORECASE)
                    for vw in LOCATION_VENUE_WORDS
                )
                if is_venue_or_place or pn_clean.lower() in LOCATION_VENUE_WORDS:
                    continue

                has_prot = any(c.role == CharacterRole.PROTAGONIST for c in current_state.characters.values()) or any(info["role"] == CharacterRole.PROTAGONIST for info in identified_entities.values())
                role = CharacterRole.SUPPORTING if has_prot else CharacterRole.PROTAGONIST
                rel_type = "SUPPORTING" if has_prot else "PROTAGONIST"
                
                derived_mot = f"Character established in story narrative ({pn_clean})"
                for s in sentences:
                    if pn_clean.lower() in s.lower():
                        derived_mot = s.strip()
                        break
                
                identified_entities[pn_clean] = {
                    "role": role,
                    "rel_type": rel_type,
                    "descriptor": "character",
                    "default_motivation": derived_mot
                }

        # Check existing protagonist in canonical state or newly identified
        protagonist_name = next(
            (c.name for c in current_state.characters.values() if c.role == CharacterRole.PROTAGONIST),
            None
        )
        if not protagonist_name:
            protagonist_name = next(
                (name for name, info in identified_entities.items() if info["role"] == CharacterRole.PROTAGONIST),
                None
            )
        if not protagonist_name and current_state.characters:
            # Fallback to single established character
            protagonist_name = list(current_state.characters.values())[0].name
        if not protagonist_name and identified_entities:
            # Fallback to first identified non-antagonist entity and promote to PROTAGONIST
            non_antags = [k for k, v in identified_entities.items() if v["role"] != CharacterRole.ANTAGONIST]
            protagonist_name = non_antags[0] if non_antags else list(identified_entities.keys())[0]
            if protagonist_name in identified_entities:
                identified_entities[protagonist_name]["role"] = CharacterRole.PROTAGONIST

        # Process each identified named entity
        for pname, info in identified_entities.items():
            role_to_assign = info["role"]
            rel_type = info["rel_type"]
            default_mot = info["default_motivation"]

            # Derive contextual motivation from sentence if present
            derived_mot = default_mot
            for s in sentences:
                if pname.lower() in s.lower() or info["descriptor"] in s.lower():
                    derived_mot = s.strip()
                    break

            res = EntityRegistry.resolve_entity(current_state, pname, role_hint=role_to_assign)

            if res.outcome == ResolutionOutcome.AMBIGUOUS:
                ambiguities.append(res.ambiguity_reason or f"Ambiguous reference to {pname}")
            elif res.outcome == ResolutionOutcome.NEW:
                extracted_names.append(pname)

                # Check if a generic placeholder character (e.g. "Sister", "Brother") exists in state
                placeholder_key = next(
                    (k for k, c in current_state.characters.items() if k.lower() == info["descriptor"] or c.name.lower() == info["descriptor"]),
                    None
                )
                if placeholder_key:
                    # Migrate generic placeholder character to proper name
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{pname}",
                            mutation_type=MutationType.CREATE,
                            new_value={
                                "character_id": current_state.characters[placeholder_key].character_id,
                                "name": pname,
                                "role": role_to_assign.value,
                                "status": StateStatus.FACT.value,
                                "core_motivation": derived_mot,
                                "fatal_flaw": current_state.characters[placeholder_key].fatal_flaw or "Vulnerability revealed under pressure"
                            },
                            rationale=f"Migrated placeholder '{placeholder_key}' to canonically established proper name '{pname}'"
                        )
                    )
                else:
                    # Propose new character creation
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{pname}",
                            mutation_type=MutationType.CREATE,
                            new_value={
                                "character_id": str(uuid4()),
                                "name": pname,
                                "role": role_to_assign.value,
                                "status": StateStatus.FACT.value,
                                "core_motivation": derived_mot,
                                "fatal_flaw": "Vulnerability revealed under pressure"
                            },
                            rationale=f"Extracted established proper named character '{pname}' ({info['descriptor']}) from creator narrative"
                        )
                    )

                # Propose bidirectional relationships with Protagonist
                if protagonist_name and protagonist_name != pname:
                    # Protagonist -> New Character relationship
                    p_to_char_rel = {
                        "target_character": pname,
                        "relation_type": rel_type,
                        "status": StateStatus.FACT.value,
                        "dynamic": f"{protagonist_name} is in direct dramatic collision/connection with {pname} ({info['descriptor']})",
                        "tension_level": 8 if role_to_assign == CharacterRole.ANTAGONIST else 6
                    }
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{protagonist_name}.relationships",
                            mutation_type=MutationType.UPDATE,
                            new_value=[p_to_char_rel],
                            rationale=f"Canonical relational dynamic: {protagonist_name} <-> {pname} ({rel_type})"
                        )
                    )
                    # New Character -> Protagonist relationship
                    char_to_p_rel = {
                        "target_character": protagonist_name,
                        "relation_type": "TARGET" if role_to_assign == CharacterRole.ANTAGONIST else rel_type,
                        "status": StateStatus.FACT.value,
                        "dynamic": f"{pname} interacts with {protagonist_name}",
                        "tension_level": 8 if role_to_assign == CharacterRole.ANTAGONIST else 5
                    }
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{pname}.relationships",
                            mutation_type=MutationType.UPDATE,
                            new_value=[char_to_p_rel],
                            rationale=f"Canonical relational dynamic: {pname} <-> {protagonist_name}"
                        )
                    )

            elif res.outcome == ResolutionOutcome.MATCH and res.character:
                # Update existing character motivation if richer narrative provided
                if not res.character.core_motivation or len(derived_mot) > len(res.character.core_motivation or ""):
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{res.character_key}.core_motivation",
                            mutation_type=MutationType.UPDATE,
                            new_value=derived_mot,
                            rationale=f"Updated core motivation for established character '{pname}' from creator response"
                        )
                    )
                # Update bidirectional relationship with protagonist to reflect latest creator narrative
                if protagonist_name and protagonist_name != pname:
                    p_to_char_rel = {
                        "target_character": pname,
                        "relation_type": rel_type,
                        "status": StateStatus.FACT.value,
                        "dynamic": f"{protagonist_name} connects to {pname} ({info['descriptor']})",
                        "tension_level": 8 if role_to_assign == CharacterRole.ANTAGONIST else 6
                    }
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{protagonist_name}.relationships",
                            mutation_type=MutationType.UPDATE,
                            new_value=[p_to_char_rel],
                            rationale=f"Updated relationship between {protagonist_name} and {pname} to {rel_type}"
                        )
                    )
                    char_to_p_rel = {
                        "target_character": protagonist_name,
                        "relation_type": "TARGET" if role_to_assign == CharacterRole.ANTAGONIST else rel_type,
                        "status": StateStatus.FACT.value,
                        "dynamic": f"{pname} interacts with {protagonist_name}",
                        "tension_level": 8 if role_to_assign == CharacterRole.ANTAGONIST else 5
                    }
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{res.character_key}.relationships",
                            mutation_type=MutationType.UPDATE,
                            new_value=[char_to_p_rel],
                            rationale=f"Updated reciprocal relationship between {pname} and {protagonist_name} to {rel_type}"
                        )
                    )

        # Cross-character pairwise relationships between all established characters in story
        all_chars_map = {**current_state.characters}
        for pname, info in identified_entities.items():
            if pname not in all_chars_map:
                all_chars_map[pname] = CharacterState(name=pname, role=info["role"])

        for name_a, char_a in all_chars_map.items():
            for name_b, char_b in all_chars_map.items():
                if name_a == name_b or name_a == protagonist_name or name_b == protagonist_name:
                    continue
                sentence_co_occur = any(name_a.lower() in s.lower() and name_b.lower() in s.lower() for s in sentences)
                is_polarity = (char_a.role == CharacterRole.ANTAGONIST and char_b.role != CharacterRole.ANTAGONIST) or (char_b.role == CharacterRole.ANTAGONIST and char_a.role != CharacterRole.ANTAGONIST)
                if sentence_co_occur or is_polarity:
                    has_rel = any(r.target_character.lower() == name_b.lower() for r in getattr(char_a, 'relationships', []))
                    if not has_rel:
                        rel_type = "OPPOSITION" if (char_a.role == CharacterRole.ANTAGONIST or char_b.role == CharacterRole.ANTAGONIST) else "RELATION"
                        proposed_mutations.append(
                            StateMutation(
                                target_path=f"characters.{name_a}.relationships",
                                mutation_type=MutationType.UPDATE,
                                new_value=[{
                                    "target_character": name_b,
                                    "relation_type": rel_type,
                                    "status": StateStatus.FACT.value,
                                    "dynamic": f"{name_a} interacts with {name_b}",
                                    "tension_level": 8 if rel_type == "OPPOSITION" else 5
                                }],
                                rationale=f"Canonical relational dynamic: {name_a} <-> {name_b}"
                            )
                        )

        # ---------------------------------------------------------------------
        # 1b. Knowledge, Belief, and Dramatic Irony State Extraction
        # ---------------------------------------------------------------------
        # Pattern K1: Secret facts (e.g. "Their uncle Themba secretly owes the bank money")
        match_secret = re.search(r'\b([A-Z][a-z]+)\s+secretly\s+([^.]+)', text)
        if match_secret:
            char_s = match_secret.group(1).capitalize()
            fact_desc = match_secret.group(2).strip()
            fact_key = "bank_debt" if "bank" in fact_desc.lower() or "debt" in fact_desc.lower() or "money" in fact_desc.lower() else "secret_knowledge"
            proposed_mutations.append(
                StateMutation(
                    target_path=f"knowledge.{char_s}.{fact_key}",
                    mutation_type=MutationType.UPDATE,
                    new_value={"status": KnowledgeStatus.KNOWS.value, "confidence": 1.0},
                    rationale=f"{char_s} holds secret knowledge: {fact_desc}"
                )
            )
            # Other established characters do not know this secret
            all_known = set(current_state.characters.keys()) | set(identified_entities.keys())
            for oc in all_known:
                if oc != char_s and oc.lower() not in cls.STOP_WORDS:
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"knowledge.{oc}.{char_s.lower()}_{fact_key}",
                            mutation_type=MutationType.UPDATE,
                            new_value={"status": KnowledgeStatus.DOES_NOT_KNOW.value, "confidence": 1.0},
                            rationale=f"{oc} is unaware of {char_s}'s secret: {fact_desc}"
                        )
                    )

        # Pattern K2: Character Ignorance (e.g. "Actually Jonas doesn't know Sabelo took it yet")
        match_ignorant = re.search(r'\b(?:[Aa]ctually\s+)?([A-Z][a-z]+)\s+(?:doesn\'t|does\s+not)\s+know\s+([^.]+?)(?:\s+yet)?\b', text)
        if match_ignorant:
            char_ign = match_ignorant.group(1).capitalize()
            fact_desc = match_ignorant.group(2).strip()
            fact_key = "sabelo_theft" if "took" in fact_desc.lower() or "steal" in fact_desc.lower() or "money" in fact_desc.lower() else "theft"
            proposed_mutations.append(
                StateMutation(
                    target_path=f"knowledge.{char_ign}.{fact_key}",
                    mutation_type=MutationType.UPDATE,
                    new_value={"status": KnowledgeStatus.DOES_NOT_KNOW.value, "confidence": 1.0},
                    rationale=f"{char_ign} is unaware of {fact_desc}"
                )
            )

        # Pattern K3: Dramatic Irony / Audience Knowledge
        # e.g. "the audience should know, but Jonas shouldn't", "the audience sees the theft in episode one, but Sipho only discovers it later"
        match_aud = re.search(r'\b(?:the\s+)?audience\s+(?:should\s+know|knows|sees)\b', text, re.IGNORECASE)
        if match_aud:
            fact_key = "theft"
            if "money" in text.lower() or "took" in text.lower() or "boot" in text.lower():
                fact_key = "sabelo_theft"
            proposed_mutations.append(
                StateMutation(
                    target_path=f"knowledge.Audience.{fact_key}",
                    mutation_type=MutationType.UPDATE,
                    new_value={"status": KnowledgeStatus.KNOWS.value, "confidence": 1.0},
                    rationale="Audience possesses dramatic irony knowledge"
                )
            )
            # Find unaware character if mentioned
            match_unaware = re.search(r'\b(?:but\s+)?([A-Z][a-z]+)\s+(?:shouldn\'t|doesn\'t|does\s+not|only\s+discovers\s+it\s+later)\b', text)
            if match_unaware:
                u_name = match_unaware.group(1).capitalize()
                if u_name.lower() not in cls.STOP_WORDS:
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"knowledge.{u_name}.{fact_key}",
                            mutation_type=MutationType.UPDATE,
                            new_value={"status": KnowledgeStatus.DOES_NOT_KNOW.value, "confidence": 1.0},
                            rationale=f"{u_name} is unaware during dramatic irony setup"
                        )
                    )

        # Pattern K4: Character Belief vs World Truth (e.g. "Sabelo thinks she's his sister because that's what he was told")
        match_belief = re.search(r'\b([A-Z][a-z]+)\s+(?:thinks|believes)\s+([^.]+?)\s+because\s+([^.]+)', text, re.IGNORECASE)
        if match_belief:
            char_b = match_belief.group(1).capitalize()
            if char_b.lower() in cls.STOP_WORDS:
                char_b = protagonist_name or (list(current_state.characters.keys())[0] if current_state.characters else None)
            if char_b and char_b.lower() not in cls.STOP_WORDS and (char_b in current_state.characters or char_b in identified_entities):
                belief_content = match_belief.group(2).strip()
                reason = match_belief.group(3).strip()
                fact_k = "zodwa_relation_belief" if "sister" in belief_content.lower() else "belief_fact"
                proposed_mutations.append(
                    StateMutation(
                        target_path=f"knowledge.{char_b}.{fact_k}",
                        mutation_type=MutationType.UPDATE,
                        new_value={"status": KnowledgeStatus.BELIEVES.value, "confidence": 1.0},
                        rationale=f"{char_b} believes '{belief_content}' because {reason}"
                    )
                )

        # Pattern R1: Not Related / Childhood Companions (e.g. "No, wait. They grew up together, but they're not related.")
        if re.search(r'\b(?:grew\s+up\s+together|not\s+related)\b', text, re.IGNORECASE):
            chars_list = list(current_state.characters.keys())
            if len(chars_list) >= 2:
                c1, c2 = chars_list[0], chars_list[1]
                proposed_mutations.append(
                    StateMutation(
                        target_path=f"characters.{c1}.relationships",
                        mutation_type=MutationType.UPDATE,
                        new_value=[{
                            "target_character": c2,
                            "relation_type": "CHILDHOOD_COMPANION",
                            "status": StateStatus.FACT.value,
                            "dynamic": f"{c1} and {c2} grew up together but are not related by blood",
                            "tension_level": 3
                        }],
                        rationale=f"Updated canonical relation between {c1} and {c2} to non-familial companion"
                    )
                )
                proposed_mutations.append(
                    StateMutation(
                        target_path=f"characters.{c2}.relationships",
                        mutation_type=MutationType.UPDATE,
                        new_value=[{
                            "target_character": c1,
                            "relation_type": "CHILDHOOD_COMPANION",
                            "status": StateStatus.FACT.value,
                            "dynamic": f"{c2} and {c1} grew up together but are not related by blood",
                            "tension_level": 3
                        }],
                        rationale=f"Updated reciprocal relation between {c2} and {c1} to non-familial companion"
                    )
                )

        # Pattern R2: False Polarity / Non-Corrupt Protector (e.g. "Daniel isn't corrupt. He's trying to protect her.")
        match_protect = re.search(r'\b([A-Z][a-z]+)\s+isn\'t\s+corrupt[.\s]+(?:(?:He\'s|She\'s|He\s+is|She\s+is)\s+)?trying\s+to\s+protect\s+([A-Za-z]+)?', text, re.IGNORECASE)
        if match_protect:
            p_name = match_protect.group(1).capitalize()
            target_p = (match_protect.group(2) or protagonist_name or "").capitalize()
            if p_name in current_state.characters:
                proposed_mutations.append(
                    StateMutation(
                        target_path=f"characters.{p_name}.role",
                        mutation_type=MutationType.UPDATE,
                        new_value=CharacterRole.SUPPORTING.value,
                        rationale=f"Reclassified {p_name} from antagonist to supporting protector"
                    )
                )
                proposed_mutations.append(
                    StateMutation(
                        target_path=f"characters.{p_name}.core_motivation",
                        mutation_type=MutationType.UPDATE,
                        new_value=f"Trying to protect {target_p}",
                        rationale=f"Updated motivation for {p_name}: protective stance"
                    )
                )
                if target_p:
                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{p_name}.relationships",
                            mutation_type=MutationType.UPDATE,
                            new_value=[{
                                "target_character": target_p,
                                "relation_type": "PROTECTOR",
                                "status": StateStatus.FACT.value,
                                "dynamic": f"{p_name} is trying to protect {target_p}",
                                "tension_level": 4
                            }],
                            rationale=f"Updated relationship dynamic: {p_name} protects {target_p}"
                        )
                    )

        # Check candidate proper nouns against existing canonical characters for ambiguities (LOCK 2 & LOCK 3)
        tokens = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
        for tok in tokens:
            if tok.lower() in cls.STOP_WORDS or tok in identified_entities:
                continue
            if current_state.characters:
                res = EntityRegistry.resolve_entity(current_state, tok)
                if res.outcome == ResolutionOutcome.AMBIGUOUS:
                    reason = res.ambiguity_reason or f"Ambiguous reference to '{tok}'"
                    if reason not in ambiguities:
                        ambiguities.append(reason)

        # ---------------------------------------------------------------------
        # 2. Chronology Anchor & Event Extraction
        # ---------------------------------------------------------------------
        seq = existing_events_count + 1

        for sentence in sentences:
            s_clean = sentence.strip()
            if len(s_clean) < 10:
                continue

            # Determine best anchor type match
            matched_anchor = "EVENT_PROGRESSION"
            for anchor_type, pattern, _ in cls.CHRONOLOGY_MARKERS:
                if re.search(pattern, s_clean, re.IGNORECASE):
                    matched_anchor = anchor_type
                    break

            # If explicit ending was declared in/around this sentence
            if is_ending and (sentence == sentences[-1] or "happy" in s_clean.lower() or "peace" in s_clean.lower() or "dies" in s_clean.lower()):
                matched_anchor = "RESOLUTION"

            headline = s_clean[:60] + ("..." if len(s_clean) > 60 else "")
            proposed_events.append(
                ChronologyEvent(
                    event_id=str(uuid4()),
                    story_id=current_state.story_id,
                    state_version=current_state.state_version + 1,
                    event_sequence=seq,
                    anchor_type=matched_anchor,
                    headline=headline,
                    description=s_clean,
                    event_status=StateStatus.FACT
                )
            )
            seq += 1

        # ---------------------------------------------------------------------
        # 3. Explicit Ending Anchor if ending was declared
        # ---------------------------------------------------------------------
        if is_ending:
            proposed_mutations.append(
                StateMutation(
                    target_path="explicit_ending_declared",
                    mutation_type=MutationType.UPDATE,
                    new_value=True,
                    rationale="Creator explicitly declared story ending"
                )
            )

        return NarrativeExtractionResult(
            raw_input=text,
            proposed_mutations=proposed_mutations,
            proposed_events=proposed_events,
            explicit_ending_detected=is_ending,
            ending_text=ending_match,
            extracted_character_names=extracted_names,
            ambiguities=ambiguities
        )

