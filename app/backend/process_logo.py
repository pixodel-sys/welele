import shutil
import os
from PIL import Image

src = r"C:\Users\Pixodel Work\.gemini\antigravity-ide\brain\b907d5b4-8775-46d5-8a3a-1e985f9b7443\.user_uploaded\media_1788799996743.jpg"
dest_dir = r"g:\App_Development\App_Dev\Welele Media\app\frontend\public\brand"
os.makedirs(dest_dir, exist_ok=True)

# 1. Save Full Lockup
shutil.copy2(src, os.path.join(dest_dir, "welele_official_logo.jpg"))
print("Saved: welele_official_logo.jpg")

# 2. Crop Mark Only
img = Image.open(src)
w, h = img.size
# Top ribbon mark
mark = img.crop((int(w * 0.16), int(h * 0.12), int(w * 0.84), int(h * 0.58)))
mark.save(os.path.join(dest_dir, "welele_official_mark.jpg"), quality=95)
print("Saved: welele_official_mark.jpg")
