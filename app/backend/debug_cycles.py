import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from story_forge.models import StoryState, CharacterState, CharacterRole
from story_forge.engine.narrative_extractor import NarrativeExtractor

s = StoryState(
    story_id='s_test4',
    characters={
        'Sabelo': CharacterState(name='Sabelo', role=CharacterRole.PROTAGONIST),
        'Zodwa': CharacterState(name='Zodwa', role=CharacterRole.CONFIDANT)
    }
)
text = "Jonas owns the money. He's dangerous, obviously, but I don't want him to just be some cartoon villain."
res = NarrativeExtractor.extract(text, s)
print("Extracted characters:", res.extracted_character_names)
for m in res.proposed_mutations:
    print(f"  {m.target_path} -> {m.new_value}")
