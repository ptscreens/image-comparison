Compare Screens -- MediaInfo + FFmpeg + guessit + Auto Upload + BBCode
==========================================================

A simple Python tool for **randomly extracting and comparing frames** from two `.mkv` files (Source & Encode). The script then **uploads** those screenshots to [ptscreens.com](https://ptscreens.com/) and outputs a **BBCode** file, wrapped in `[center] ... [/center]` formatting, so you can easily share side-by-side comparisons on forums.

Features
--------

-   **Tkinter Dialogs**:
    -   Pick your Source and Encode `.mkv` files from GUI file dialogs.
    -   Prompt (via a GUI "askinteger" box) for how many random frames to extract.
-   **MediaInfo** for frame count & average FPS:
    -   Grabs `FrameCount` and `FrameRate` from your `.mkv` files without relying on `ffprobe`.
-   **GPU-Accelerated Extraction**:
    -   Uses `ffmpeg -hwaccel cuda -ss <timestamp> -frames:v 1 ...` for **fast-seeking** random frames.
-   **Two-Phase**:
    -   Extract **all** frames first.
    -   Upload them **after** extraction completes.
-   **guessit** for Subfolder Naming**:
    -   Parse the Source filename's "movie name" & "year," creating a folder like:

        ```
        .\Screens\MovieName (MovieYear)

        ```

-   **Wrapped BBCode** in `[center] ... [/center]`:
    -   Begins with a heading, `SOURCE | ENCODE`.
    -   Then each line is `[url=SRC_URL][img=300]SRC_URL[/img][/url] [url=ENC_URL][img=300]ENC_URL[/img][/url]`.

Prerequisites
-------------

1.  **Python 3.7+**
2.  **MediaInfo CLI** installed and on your **system PATH**
3.  **ffmpeg** on your PATH (with optional **GPU** decoding support)
4.  **`pip install -r requirements.txt`**
    -   The `requirements.txt` should contain something like:

        ```
        guessit==3.5.1
        requests==2.31.0

        ```

5.  A **ptscreens.com** (Chevereto) **API Key**, placed in the script as `IMG_HOST_API_KEY`.

Usage
-----

1.  **Clone** or **download** the repository containing this script (e.g., `compare_screens_mediainfo.py`).
2.  **Install** the Python dependencies:

    ```
    pip install -r requirements.txt

    ```

    OR (Run Powershell as Administrator)

    ```
    ./requirements.ps1 

    ```    

4.  **Check** that `mediainfo --version` and `ffmpeg -version` work in your terminal.
5.  **Open** the script, locate the line:

    ```
    IMG_HOST_API_KEY = "<YOUR_API_KEY_HERE>"

    ```

    and paste in your actual ptscreens API key.
6.  **Run** the script:

    ```
    python compare_screens_mediainfo.py

    ```

7.  A **GUI** window appears, asking you to:
    -   Select your **Source** `.mkv` file.
    -   Select your **Encode** `.mkv` file.
    -   Enter how many random frames to extract (via a small integer dialog).
8.  The script:
    -   Retrieves total frame counts & FPS from **MediaInfo**.
    -   Randomly selects the requested number of frames from `1..min(FrameCountSource, FrameCountEncode)`.
    -   **Extracts** those frames for both Source & Encode.
    -   **Uploads** all the resulting `.png` screenshots to ptscreens.com.
    -   **Writes** a `Comparison_BBCode.txt` in `.\Screens\MovieName (MovieYear)\` which is fully wrapped in:

        ```
        [center]
        SOURCE  |  ENCODE

        [url=SourceImageURL][img=300]SourceImageURL[/img][/url]    [url=EncodeImageURL][img=300]EncodeImageURL[/img][/url]
        ...
        [/center]

        ```

    -   All screenshots are also saved there as `.png` files.

Example Output Structure
------------------------

```
Screens/
└── MovieName (MovieYear)/
    ├── Source_frame1025.png
    ├── Source_frame27541.png
    ├── Encode_frame1025.png
    ├── Encode_frame27541.png
    └── Comparison_BBCode.txt

```

Inside **`Comparison_BBCode.txt`**:

```
[center]
SOURCE  |  ENCODE

[url=https://img.ptscreens.com/abc123.png][img=300]https://img.ptscreens.com/abc123.png[/img][/url]    [url=https://img.ptscreens.com/def456.png][img=300]https://img.ptscreens.com/def456.png[/img][/url]
[url=https://img.ptscreens.com/ghijkl.png][img=300]https://img.ptscreens.com/ghijkl.png[/img][/url]    [url=https://img.ptscreens.com/zyx987.png][img=300]https://img.ptscreens.com/zyx987.png[/img][/url]

[/center]

```

Notes & Caveats
---------------

-   **GPU Acceleration**: If you don't have an NVIDIA GPU or `-hwaccel cuda` fails, remove or replace that parameter (e.g., `-hwaccel dxva2` on Windows with certain AMD or Intel drivers).
-   **Frame Accuracy**: For variable-frame-rate files, random seeking by frame index may be slightly off. This script assumes **constant** frame rate.
-   **License**: This is a personal or sample script. Ensure you comply with [ffmpeg's license](https://ffmpeg.org/legal.html) and [MediaInfo's license](https://mediaarea.net/en/MediaInfo/License).

Contributing
------------

-   **Issues/Ideas**: Open an Issue or Pull Request if you find bugs or want additional features (like partial Timestamps or custom naming).
-   **Testing**: We welcome tests on various MKV sources, different GPU acceleration settings, and large frame counts.

Enjoy effortless Source/Encode comparisons, and let us know if you need help!
