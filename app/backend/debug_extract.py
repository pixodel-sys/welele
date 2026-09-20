import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from story_forge.models import StoryState, CharacterState, CharacterRole, StateStatus
from story_forge.engine.narrative_extractor import NarrativeExtractor

s = StoryState(story_id="t1", title="T", logline="L")
s.characters["Sabelo"] = CharacterState(name="Sabelo", role=CharacterRole.PROTAGONIST, status=StateStatus.FACT)
s.characters["Zodwa"] = CharacterState(name="Zodwa", role=CharacterRole.CONFIDANT, status=StateStatus.FACT)
s.characters["Jonas"] = CharacterState(name="Jonas", role=CharacterRole.ANTAGONIST, status=StateStatus.FACT)

text = "Zodwa is not Sabelo's sister. She is his girlfriend."
res = NarrativeExtractor.extract(text, s)
print("Extracted character names:", res.extracted_character_names)
for m in res.proposed_mutations:
    print("Mutation:", m.target_path, "->", m.new_value)
