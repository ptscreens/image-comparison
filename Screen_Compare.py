#!/usr/bin/env python3
#
# 1. Tkinter dialogs -> pick Source & Encode.
# 2. Asks how many random frames to extract (via MediaInfo for total frames & fps).
# 3. Extract ALL screenshots first (fast-seek GPU in ffmpeg).
# 4. Intelligently crop black bars from top and bottom of Source screenshots.
# 5. Then upload all screenshots to and image host (IMG_HOST).
# 6. Write BBCode lines to:
#       .\Screens\MovieName (MovieYear)\Comparison_BBCode.txt
#    The entire document is wrapped in [center]...[/center],
#    and starts with a line "SOURCE  |  ENCODE".

import os
import re
import random
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog
import requests
from guessit import guessit
from PIL import Image  # Import Pillow for image processing

###############################################################################
# CONFIG
###############################################################################
IMG_HOST_API_KEY = "<YOUR_API_KEY_HERE>"   # <-- Set your Image Host API key
IMG_HOST_UPLOAD_URL = "https://ptscreens.com/api/1/upload"
#IMG_HOST_UPLOAD_URL = "https://imgoe.download/api/1/upload"


FFMPEG_CMD = "ffmpeg"
MEDIAINFO_CMD = "mediainfo"

# Cropping parameters
CROP_THRESHOLD = 30          # Pixel intensity threshold for considering non-black
MIN_NON_BLACK_RATIO = 0.05   # Minimum ratio of non-black pixels to consider a row as non-black

###############################################################################
# FUNCTIONS
###############################################################################

def get_total_frames_mediainfo(video_path):
    """
    Use MediaInfo to retrieve (total_frames, fps).
    - mediainfo --Inform="Video;%FrameCount%" <file>
    - mediainfo --Inform="Video;%FrameRate%"  <file>
    Return (0, 0) if fails.
    """
    try:
        # 1) total frames
        cmd_frames = [MEDIAINFO_CMD, '--Inform=Video;%FrameCount%', video_path]
        res1 = subprocess.run(cmd_frames, capture_output=True, text=True, check=True)
        frames_str = res1.stdout.strip()
        try:
            total_frames = int(frames_str)
        except ValueError:
            return 0, 0

        # 2) fps
        cmd_fps = [MEDIAINFO_CMD, '--Inform=Video;%FrameRate%', video_path]
        res2 = subprocess.run(cmd_fps, capture_output=True, text=True, check=True)
        fps_str = res2.stdout.strip()
        try:
            fps = float(fps_str)
        except ValueError:
            return 0, 0

        if total_frames > 0 and fps > 0:
            return total_frames, fps

    except Exception as e:
        print(f"[ERROR] MediaInfo failed on {video_path}: {e}")
    return 0, 0


def parse_filename_guessit(file_path):
    """
    Parse the Source filename with guessit -> (title, year).
    We'll form a subfolder name like "MovieName (MovieYear)" from these.
    """
    base_name = os.path.basename(file_path)
    info = guessit(base_name)
    title = info.get('title')
    year = info.get('year')
    if year and isinstance(year, int):
        year = str(year)
    return title, year


def seconds_to_hhmmss_ms(sec):
    """
    Convert float seconds -> "HH:MM:SS.mmm"
    """
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


def extract_frame_fastseek_gpu(video_path, frame_number, fps, output_path):
    """
    Use ffmpeg w/ GPU fast-seek:  -hwaccel cuda -ss <timestamp> -frames:v 1 ...
    """
    timestamp = (frame_number - 1) / fps  # 1-based index
    seek_str = seconds_to_hhmmss_ms(timestamp)

    cmd = [
        FFMPEG_CMD,
        '-hwaccel', 'cuda',
        '-ss', seek_str,
        '-i', video_path,
        '-frames:v', '1',
        '-an', '-sn',
        '-loglevel', 'error',
        '-y',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)


def intelligently_crop_top_bottom(image_path, output_path, threshold=30, min_ratio=0.05):
    """
    Intelligently crop black bars from the top and bottom of the image.
    Only removes black bars from top and bottom; side borders are left untouched.
    Parameters:
        - threshold: Pixel intensity above which a pixel is considered non-black.
        - min_ratio: Minimum ratio of non-black pixels in a row to consider it as content.
    """
    try:
        with Image.open(image_path) as img:
            gray = img.convert("L")
            width, height = gray.size

            # Function to find the first row from top/bottom with sufficient non-black pixels
            def find_boundary(start, end, step):
                for y in range(start, end, step):
                    row = gray.crop((0, y, width, y + 1))
                    non_black = sum(pixel > threshold for pixel in row.getdata())
                    if (non_black / width) >= min_ratio:
                        return y
                return None

            # Find top boundary
            top = find_boundary(0, height, 1)
            if top is None:
                top = 0  # No content found; don't crop
            else:
                print(f"     [INFO] Top boundary detected at row {top}")

            # Find bottom boundary
            bottom = find_boundary(height - 1, -1, -1)
            if bottom is None:
                bottom = height  # No content found; don't crop
            else:
                print(f"     [INFO] Bottom boundary detected at row {bottom}")

            # Define crop box: (left, top, right, bottom)
            crop_box = (0, top, width, bottom + 1)

            # Validate crop_box to ensure we're not removing too much
            cropped_height = bottom - top + 1
            if cropped_height / height < 0.3:
                print(f"     [WARN] Cropped height {cropped_height} is less than 30% of original height. Skipping cropping.")
                img.save(output_path)
            else:
                # Crop and save
                cropped_img = img.crop(crop_box)
                cropped_img.save(output_path)
                print(f"     [INFO] Image cropped: {crop_box}")

    except Exception as e:
        print(f"[ERROR] Cropping failed for {image_path}: {e}")
        # In case of error, save the original image
        with Image.open(image_path) as img:
            img.save(output_path)


def upload_to_img_host(image_path, api_key):
    """
    Upload the given screenshot to your image host, returning direct URL or None.
    """
    try:
        with open(image_path, "rb") as f:
            data = {"key": api_key}
            files = {"source": (os.path.basename(image_path), f, "image/png")}
            r = requests.post(IMG_HOST_UPLOAD_URL, data=data, files=files, timeout=15)
            r.raise_for_status()
            j = r.json()
            if "image" in j and "url" in j["image"]:
                return j["image"]["url"]
            else:
                print(f"[WARN] Missing 'image.url' in response for {image_path}: {j}")
                return None
    except Exception as e:
        print(f"[ERROR] Upload for {image_path}: {e}")
        return None

###############################################################################
# MAIN
###############################################################################

def main():
    print("\n=== Compare Source/Encode with MediaInfo + GPU + Auto Upload ===\n")

    # Check API key
    if not IMG_HOST_API_KEY or IMG_HOST_API_KEY.startswith("<YOUR_API_KEY_HERE>"):
        print("[ERROR] Please set your ptscreens.com API key in the script. Exiting.")
        return

    # Setup Tkinter
    root = tk.Tk()
    root.withdraw()

    # 1) Pick Source
    print("Select SOURCE .mkv file...")
    source_file = filedialog.askopenfilename(
        title="Select Source .mkv",
        filetypes=[("MKV files", "*.mkv")]
    )
    if not source_file:
        print("[INFO] No Source selected. Exiting.")
        return
    print(f"[INFO] Source: {source_file}")

    # 2) Pick Encode
    print("\nSelect ENCODE .mkv file...")
    encode_file = filedialog.askopenfilename(
        title="Select Encode .mkv",
        filetypes=[("MKV files", "*.mkv")]
    )
    if not encode_file:
        print("[INFO] No Encode selected. Exiting.")
        return
    print(f"[INFO] Encode: {encode_file}\n")

    # 3) Ask how many frames
    print("Asking how many random frames to extract...\n")
    frames_count = simpledialog.askinteger(
        "Number of Screens",
        "How many random frames would you like to extract?",
        initialvalue=6, minvalue=1, maxvalue=9999,
        parent=root
    )
    root.update()  # ensure dialog fully closes
    if frames_count is None:
        print("[INFO] User canceled frames count. Exiting.")
        return
    print(f"[INFO] User requested {frames_count} frames.\n")

    # 4) Gather total frames/fps from MediaInfo
    print("[INFO] Gathering total frames & fps (MediaInfo)...\n")
    s_total, s_fps = get_total_frames_mediainfo(source_file)
    e_total, e_fps = get_total_frames_mediainfo(encode_file)
    if s_total <= 0 or s_fps <= 0:
        print("[ERROR] Invalid frames/fps for Source. Exiting.")
        return
    if e_total <= 0 or e_fps <= 0:
        print("[ERROR] Invalid frames/fps for Encode. Exiting.")
        return

    print(f"Source -> total_frames={s_total}, fps={s_fps}")
    print(f"Encode -> total_frames={e_total}, fps={e_fps}\n")

    # 5) If frames_count > min, clamp it
    min_total = min(s_total, e_total)
    if frames_count > min_total:
        frames_count = min_total
        print(f"[WARN] Requested frames exceed available. Limiting to {min_total}.\n")

    # Pick random frames
    chosen_frames = random.sample(range(1, min_total + 1), frames_count)
    chosen_frames.sort()
    print(f"[INFO] Chosen frames: {chosen_frames}\n")

    # 6) Determine subfolder: .\Screens\MovieName (MovieYear)
    g_title, g_year = parse_filename_guessit(source_file)
    if g_title:
        safe_title = re.sub(r'[\\/:*?"<>|]+', '', g_title).strip()
        folder_name = safe_title if safe_title else "Unknown Movie"
        if g_year:
            folder_name += f" ({g_year})"
    else:
        folder_name = "Unknown Movie"

    base_dir = os.path.dirname(os.path.abspath(__file__))  # script's directory
    screens_dir = os.path.join(base_dir, "Screens")
    os.makedirs(screens_dir, exist_ok=True)

    out_dir = os.path.join(screens_dir, folder_name)
    os.makedirs(out_dir, exist_ok=True)

    print(f"[INFO] Screens & BBCode will be stored in:\n  {out_dir}\n")

    # 7) Extract all screenshots first
    print(f"[INFO] Extracting {frames_count} frames for both files (fast-seek GPU)...")
    source_screens = []
    encode_screens = []

    for idx, frame_num in enumerate(chosen_frames, start=1):
        print(f"   -> Extracting frame {frame_num} ({idx}/{frames_count})")

        # Source
        src_out = os.path.join(out_dir, f"Source_frame{frame_num}.png")
        extract_frame_fastseek_gpu(source_file, frame_num, s_fps, src_out)
        print(f"     Extracted Source frame {frame_num} to {os.path.basename(src_out)}")

        # Encode
        enc_out = os.path.join(out_dir, f"Encode_frame{frame_num}.png")
        extract_frame_fastseek_gpu(encode_file, frame_num, e_fps, enc_out)
        print(f"     Extracted Encode frame {frame_num} to {os.path.basename(enc_out)}")

        source_screens.append(src_out)
        encode_screens.append(enc_out)

    print("[INFO] Extraction complete.\n")

    # 8) Intelligently crop black bars from Source screenshots only (top & bottom)
    print("[INFO] Cropping black bars from Source screenshots (top & bottom only)...\n")
    for img_path in source_screens:
        print(f"   -> Cropping {os.path.basename(img_path)}")
        intelligently_crop_top_bottom(img_path, img_path, threshold=CROP_THRESHOLD, min_ratio=MIN_NON_BLACK_RATIO)

    print("[INFO] Cropping complete.\n")

    # 9) Now upload them all
    print("[INFO] Uploading all extracted images to your image host...\n")
    src_urls = []
    enc_urls = []

    for i in range(frames_count):
        print(f"   -> Uploading pair {i+1}/{frames_count} ...")
        src_url = upload_to_img_host(source_screens[i], IMG_HOST_API_KEY) or "UPLOAD_FAILED"
        enc_url = upload_to_img_host(encode_screens[i], IMG_HOST_API_KEY) or "UPLOAD_FAILED"

        src_urls.append(src_url)
        enc_urls.append(enc_url)

    # 10) Write out the BBCode file in the same subfolder, with heading & center wrapper
    bbcode_path = os.path.join(out_dir, "Comparison_BBCode.txt")
    print(f"\n[INFO] Writing BBCode lines to {bbcode_path}...\n")

    with open(bbcode_path, "w", encoding="utf-8") as f:
        # Start with [center] and heading
        f.write("[center]\n")
        f.write("SOURCE  |  ENCODE\n\n")

        # Then each line of BBCode
        for i in range(frames_count):
            line = (
                f"[url={src_urls[i]}][img=300]{src_urls[i]}[/img][/url]    "
                f"[url={enc_urls[i]}][img=300]{enc_urls[i]}[/img][/url]"
            )
            f.write(line + "\n")

        # End center block
        f.write("\n[/center]\n")

    print("[DONE] All frames extracted, cropped, uploaded & BBCode saved.\n")
    print(f"       => Folder: {out_dir}")
    print(f"       => BBCode: {bbcode_path}\n")


if __name__ == "__main__":
    main()
