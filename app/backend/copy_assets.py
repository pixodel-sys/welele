import shutil
import glob
import os

brain_dir = r"C:\Users\Pixodel Work\.gemini\antigravity-ide\brain\b907d5b4-8775-46d5-8a3a-1e985f9b7443"
frontend_public = r"g:\App_Development\App_Dev\Welele Media\app\frontend\public"

mapping = {
    "posters/blood_ties.jpg": "blood_ties_poster*.jpg",
    "posters/ceo_secret_wife.jpg": "ceo_secret_wife_poster*.jpg",
    "posters/zulu_love_story.jpg": "zulu_love_story_poster*.jpg",
    "posters/broken_vows.jpg": "broken_vows_poster*.jpg",
    "posters/the_hustlers.jpg": "the_hustlers_poster*.jpg",
    "posters/campus_royals.jpg": "campus_royals_poster*.jpg",
    "posters/barrio_billionaire.jpg": "barrio_billionaire_poster*.jpg",
    "posters/heist_game.jpg": "heist_game_poster*.jpg",
    "banners/blood_ties_banner.jpg": "blood_ties_banner*.jpg",
    "banners/ceo_secret_wife_banner.jpg": "ceo_secret_wife_banner*.jpg",
}

for dest, pat in mapping.items():
    matches = glob.glob(os.path.join(brain_dir, pat))
    if matches:
        dest_path = os.path.join(frontend_public, dest)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(matches[-1], dest_path)
        print(f"Copied: {os.path.basename(matches[-1])} -> {dest_path}")
    else:
        print(f"Pattern not found: {pat}")
