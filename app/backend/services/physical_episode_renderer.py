"""
Welele Media™ — Physical Episode 1 Video & Audio Synthesizer
Generates the complete 88-second 9:16 vertical video master:
- Uses OpenCV for smooth Ken-Burns vertical camera motion (1080x1920 @ 24fps)
- Overlays scene timecodes, character badges, and verbatim canonical dialogue subtitles
- Generates the complete 88.0s multi-harmonic 68 BPM Zulu drum heartbeat score
- Muxes into playable H.264/AAC MP4 video master using FFmpeg
Artifact: Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4
"""

import os
import math
import struct
import wave
import subprocess
import cv2
import numpy as np

OUTPUT_DIR = r"g:\App_Development\App_Dev\Welele Media\app\backend\media_storage\renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)
FINAL_MP4_PATH = os.path.join(OUTPUT_DIR, "Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4")

FFMPEG_BIN = r"C:\Users\Pixodel Work\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"

KEYFRAME_PATHS = {
    1: r"C:\Users\Pixodel Work\.gemini\antigravity-ide\brain\aba9b41b-351d-4a06-a72e-c51fdc787c0d\thandiwe_scene1_1790516185628.jpg",
    2: r"C:\Users\Pixodel Work\.gemini\antigravity-ide\brain\aba9b41b-351d-4a06-a72e-c51fdc787c0d\bhekisisa_scene2_1790516209480.jpg",
    3: r"C:\Users\Pixodel Work\.gemini\antigravity-ide\brain\aba9b41b-351d-4a06-a72e-c51fdc787c0d\climax_scene3_1790516242870.jpg"
}

def generate_canonical_score(wav_path: str, duration_s: float = 88.0):
    """
    Synthesizes the complete 88-second score:
    - 68 BPM Zulu acoustic heartbeat drum pulse (55Hz / 110Hz)
    - Staccato cello tension from 15s to 50s
    - String tremolo and brass crescendo from 50s to 87.5s
    - Abrupt hard cut to silence at 88.0s
    """
    sample_rate = 44100
    n_samples = int(duration_s * sample_rate)
    bpm = 68.0
    beat_interval = 60.0 / bpm

    samples = []
    for i in range(n_samples):
        t = i / sample_rate

        # 1. Base Zulu drum heartbeat
        beat_phase = (t % beat_interval) / beat_interval
        p1 = math.exp(-beat_phase * 20) * math.sin(2 * math.pi * 55 * beat_phase)
        p2 = 0
        if beat_phase > 0.28:
            p2_phase = beat_phase - 0.28
            p2 = 0.7 * math.exp(-p2_phase * 22) * math.sin(2 * math.pi * 65 * p2_phase)
        drum = (p1 + p2) * 0.45

        # 2. Cello tension entering at 15s
        cello = 0.0
        if t >= 15.0:
            vol = min(1.0, (t - 15.0) / 10.0) * 0.35
            cycle = (t % (beat_interval * 2)) / (beat_interval * 2)
            f_cello = 110.0 if cycle < 0.5 else 146.8
            cello = math.sin(2 * math.pi * f_cello * t) * (math.exp(-(t % (beat_interval / 2)) * 6)) * vol

        # 3. String tremolo & Brass crescendo from 50s
        crescendo = 0.0
        if 50.0 <= t < 87.6:
            intensity = ((t - 50.0) / 37.6) ** 1.6
            d1 = math.sin(2 * math.pi * 220.0 * t)
            d2 = math.sin(2 * math.pi * 277.18 * t) # C#4 tension dissonance
            d3 = math.sin(2 * math.pi * 440.0 * t)
            tremolo = (1.0 + 0.3 * math.sin(2 * math.pi * 14.0 * t))
            crescendo = (d1 + 0.6 * d2 + 0.4 * d3) * tremolo * intensity * 0.4

        # 4. Sudden paywall silence at 87.8s -> 88.0s
        if t >= 87.8:
            fade_out = max(0.0, 1.0 - (t - 87.8) / 0.2)
            mixed = (drum + cello + crescendo) * fade_out
        else:
            mixed = drum + cello + crescendo

        mixed = max(-0.95, min(0.95, mixed))
        samples.append(int(mixed * 32767.0))

    with wave.open(wav_path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def render_all_shots_video(temp_video_path: str):
    """
    Renders 88 seconds (2112 frames @ 24fps) across 3 canonical scenes:
    - Shot 1: 00:00 - 00:15 (15s = 360 frames) -> Midnight delivery & royal ink-mark
    - Shot 2: 00:15 - 00:50 (35s = 840 frames) -> Dawn convoy & Bhekisisa confrontation
    - Shot 3: 00:50 - 00:88 (38s = 912 frames) -> Threshold climax & 88s paywall cut
    """
    w, h = 1080, 1920
    fps = 24.0
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (w, h))

    img1 = cv2.imread(KEYFRAME_PATHS[1])
    img2 = cv2.imread(KEYFRAME_PATHS[2])
    img3 = cv2.imread(KEYFRAME_PATHS[3])

    total_frames = int(88.0 * fps)
    print(f"[Video Synthesizer] Rendering {total_frames} frames (88.0s @ 24fps, 1080x1920)...")

    for f_idx in range(total_frames):
        t = f_idx / fps

        # Determine active scene and base image
        if t < 15.0:
            # Shot 1: Midnight Delivery
            scene_num = 1
            progress = t / 15.0
            zoom = 1.0 + (progress * 0.12)  # Slow Ken Burns push-in
            base_img = img1
            scene_tag = "SCENE 1: MOFOLO SOUTH CLINIC - 00:00"
            sub_title = "[VO]: In Soweto, blood is thicker than gold... but at dawn, gold came to collect."
            badge_text = "ROYAL INK-MARK DISCOVERY (PLANTED)"
            badge_color = (0, 165, 255) # Amber
        elif t < 50.0:
            # Shot 2: Dawn Convoy Confrontation
            scene_num = 2
            progress = (t - 15.0) / 35.0
            zoom = 1.0 + (progress * 0.10)
            base_img = img2
            scene_tag = "SCENE 2: CLINIC EXTERIOR GATE - 00:15"
            sub_title = "THANDIWE: 'A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa.'"
            badge_text = "BHEKISISA CONFRONTATION & CASH BRIEFCASE"
            badge_color = (180, 180, 180) # Slate
        else:
            # Shot 3: Threshold Stand-off & Paywall Freeze
            scene_num = 3
            progress = (t - 50.0) / 38.0
            zoom = 1.0 + (progress * 0.08)
            base_img = img3
            scene_tag = "SCENE 3: CLINIC THRESHOLD STAND-OFF - 00:50"
            sub_title = "CLIFFHANGER: Will Thandiwe sign the settlement or trigger a township uprising?"
            badge_text = "CUSTOMARY REGISTER LEDGER RAISED • 88s PAYWALL FREEZE"
            badge_color = (0, 0, 255) # Red

        # Ken-Burns crop and scale
        ih, iw = base_img.shape[:2]
        crop_w = int(iw / zoom)
        crop_h = int(ih / zoom)
        cx = iw // 2
        cy = ih // 2
        x1 = max(0, cx - crop_w // 2)
        y1 = max(0, cy - crop_h // 2)
        cropped = base_img[y1:y1+crop_h, x1:x1+crop_w]
        frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

        # Subtle dark gradient at top and bottom for text legibility
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 180), (0, 0, 0), -1)
        cv2.rectangle(overlay, (0, h - 260), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Header Watermark & Brand
        cv2.putText(frame, "WELELE MEDIA — ISIBUSISO EPISODE 1", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, scene_tag, (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (200, 200, 200), 2, cv2.LINE_AA)

        # Timecode display
        tc_str = f"TIMECODE: 00:{int(t):02d}:{(int(t*24)%24):02d} / 00:88:00 (9:16 VERTICAL)"
        cv2.putText(frame, tc_str, (w - 580, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)

        # Status badge
        cv2.putText(frame, badge_text, (50, h - 180), cv2.FONT_HERSHEY_SIMPLEX, 0.75, badge_color, 2, cv2.LINE_AA)

        # Subtitle Dialogue Text (Wrapped)
        words = sub_title.split(" ")
        lines = []
        cur_line = ""
        for word in words:
            if len(cur_line + " " + word) > 48:
                lines.append(cur_line)
                cur_line = word
            else:
                cur_line = (cur_line + " " + word).strip()
        if cur_line:
            lines.append(cur_line)

        y_sub = h - 120
        for line in lines[:2]:
            cv2.putText(frame, line, (50, y_sub), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)
            y_sub += 45

        # Paywall freeze indicator at 86-88s
        if t >= 86.0:
            cv2.rectangle(frame, (50, h//2 - 60), (w - 50, h//2 + 60), (0, 0, 180), -1)
            cv2.putText(frame, "PAYWALL CLIFFHANGER LOCK [88.0s]", (110, h//2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3, cv2.LINE_AA)

        out.write(frame)

        if f_idx % 240 == 0:
            print(f"  Frame {f_idx}/{total_frames} ({t:.1f}s / 88.0s)...")

    out.release()
    print("[Video Synthesizer] Raw video track rendered successfully.")


def assemble_canonical_master_mp4():
    """Combines raw video with synthesized 68 BPM Zulu audio score into H.264/AAC MP4."""
    temp_dir = os.path.join(OUTPUT_DIR, "temp_render")
    os.makedirs(temp_dir, exist_ok=True)

    temp_video = os.path.join(temp_dir, "raw_video.mp4")
    temp_audio = os.path.join(temp_dir, "score_88s.wav")

    print("\n--- Step 1: Synthesizing Canonical Score ---")
    generate_canonical_score(temp_audio, duration_s=88.0)

    print("\n--- Step 2: Rendering 88-Second 9:16 Video Frames ---")
    render_all_shots_video(temp_video)

    print(f"\n--- Step 3: Encoding & Muxing H.264 / AAC Master -> {FINAL_MP4_PATH} ---")
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", temp_video,
        "-i", temp_audio,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        FINAL_MP4_PATH
    ]
    subprocess.run(cmd, check=True)

    size_mb = os.path.getsize(FINAL_MP4_PATH) / (1024 * 1024)
    print("\n" + "="*70)
    print("SUCCESS: REAL PLAYABLE EPISODE 1 MP4 PRODUCED!")
    print(f"Artifact File: {FINAL_MP4_PATH}")
    print(f"File Size:     {size_mb:.2f} MB")
    print(f"Aspect Ratio:  9:16 Vertical (1080x1920 Native)")
    print(f"Total Runtime: 88.0 Seconds")
    print(f"Audio Track:   68 BPM Zulu Heartbeat Drum Pulse + Staccato Cello + Crescendo")
    print("="*70 + "\n")

    return FINAL_MP4_PATH

if __name__ == "__main__":
    assemble_canonical_master_mp4()
