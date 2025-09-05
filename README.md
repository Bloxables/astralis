Version: 1.0  
Created by Bloxables  

**License:** Source-available. Personal use and local modification allowed. Redistribution prohibited. See `LICENSE.txt`.

## Overview

Astralis is a Windows-only helper for Roblox that:

* reads on-screen text (OCR) in a small “target” area,
* decides whether the encounter matches your enabled items,
* if it matches: opens **Bag → Pokéballs**, selects your chosen ball, and hits **Use**,
* if it doesn’t: clicks **Run**.

Everything is configurable (regions, thresholds, items, presets), and the app includes a status overlay, a region-visualization overlay, logs, and global hotkeys.

## What’s new in this version (revamped logic)

* **OCR-based detection**: Uses Tesseract via `pytesseract` on a targeted region to read encounter names. Fuzzy matching handles typos/variants.
* **Smarter encounter flow**:
  * Detects the Bag icon appearing (rising edge) to mark a new encounter.
  * Caches text seen **before** the Bag and **during** the encounter; matches against your enabled list.
  * If matched → open Bag, select ball, press Use. If not matched for a moment → auto **Run**.
* **Robust flee handling**: Detects “You have successfully fled!” with a cooldown so encounters aren’t double-counted.
* **Two overlays**:
  * **Status overlay** (topmost but auto-hides if Roblox isn’t visible): status, poll rate, chosen ball, and a summary of enabled items.
  * **Region overlay** (F10): draws target/HUD/balls/use/bagHUD/runHUD rectangles on top of Roblox to help you tune regions.
* **Global hotkeys** (work while unfocused):  
  F6 = Pause/Resume • F7 = Exit • F10 = Toggle region overlay
* **Logs + stats**: Color-coded encounter log and counters for total encounters and item encounters.
* **Safer config UX**: Settings tab with a **Reset → 5s preview → Save** pattern. Presets show item thumbnails.

## Requirements

* Windows 10/11 (64-bit).
* Roblox desktop client.
* **Tesseract OCR 5+** installed.  
  - Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`  
  - Astralis will auto-detect Tesseract if it’s on your PATH or in the default install folder.  
  - If it’s missing, Astralis shows a UI prompt and can launch the installer automatically.  

If running from source: Python 3.9+ with `opencv-python`, `numpy`, `mss`, `pytesseract`, and Tk (bundled with Python on Windows).  
Example:  
```sh
pip install opencv-python numpy mss pytesseract
````

## Installation

**Option A — Prebuilt EXE:**

1. Download `Astralis.exe` and place an `assets` folder next to it.
   On first launch, assets are copied to `%APPDATA%\Astralis v1.0\assets\`.
2. Ensure Tesseract OCR is installed:

   * If you downloaded the release `.zip`, it may include `tesseract-setup.exe`. Run this once to install Tesseract system-wide.
   * If it’s missing, Astralis will prompt you and link to the official installer page:
     [UB Mannheim Tesseract builds](https://github.com/UB-Mannheim/tesseract/wiki).

**Option B — Python script:**

1. Place an `assets` folder next to the script.
2. Run `python astralis.py`. Assets seed into the AppData location.
3. Install Tesseract OCR 5+ before running.

On startup you’ll see a one-time **“Before You Start”** dialog with quick steps and a Discord link (`https://discord.gg/fxwzgSDvjG`). Confirm to continue.

## Tesseract OCR Notes

Astralis relies on [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text recognition.

* The Windows installer included in the release (`tesseract-setup.exe`) is provided for convenience. It comes from the UB Mannheim project.
* You may also install or update Tesseract directly from their [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki).
* Astralis will check for Tesseract automatically at startup. If not found:

  * If `tesseract-setup.exe` is next to Astralis, it will auto-run the installer.
  * Otherwise, a popup appears with a link to the download page.

**Without Tesseract installed, Astralis cannot read encounters.**

---

## Data & Folders

All runtime data lives under:

* `%APPDATA%\Astralis v1.0\` (marker file `.astralis_marker` is dropped here)
* `%APPDATA%\Astralis v1.0\settings.ini`
* `%APPDATA%\Astralis v1.0\assets\`

  * `nobg\` → item icons for the **Find** tab (single, no background)
  * `pokeballs\` → in-game ball templates (used to click inside Bag)
  * `pokeballsnobg\` → ball thumbnails for the **Use** tab
  * `other\` → UI templates: `bag.png`, `use.png`, `run.png`, optional `Astralis.png` (window icon)

On launch, older `%APPDATA%\Astralis vX.Y\` folders are cleaned up automatically if they look like previous Astralis data.

## UI at a glance

* **Find tab**: Checkbox list of items (from `assets\nobg\`). “Select all”, “Deselect all”, and **Presets**.
* **Use tab**: Choose exactly one Pokéball (from `assets\pokeballsnobg\`). The app matches the **game** template from `assets\pokeballs\` when clicking in Bag.
* **Logs tab**: Scrollable log of encounters. Green = captured target (matched), Red = ran. Stats shown below.
* **Settings tab**: Thresholds, regions, preset names. **Reset** (temporary preview) and **Save**.

## Quick start

1. In Roblox, open **Menu → Bag → Pokéballs** (important for initial ball selection visibility).
2. Close in-game chat (upper-left) so it doesn’t occlude UI.
3. Move to your target spot and start your hunt command (e.g., `;hunt`).
4. Launch Astralis.
5. On **Find**, enable items or apply a preset.
6. On **Use**, pick a Pokéball (or leave blank for auto/default).
7. Click **Start**. Use **F6** to pause/resume; **F7** to exit.

## How detection works (high level)

* **OCR target region**: Default `target_region = 0,0.75,0.6,1` (bottom-left area). White text is isolated (HSV threshold) and fed to Tesseract.
* **Name matching**: Your enabled items are normalized and compared with fuzzy matching to the OCR text stream (pre-Bag and during the encounter).
* **Bag/run detection**: Template matching finds Bag/Run inside the **HUD region** split into two halves:

  * `bag_hud_region = 0,0,0.50,1` (left half of HUD)
  * `run_hud_region = 0.50,0,1,1` (right half of HUD)
* **Flow**:

  * If a target name is recognized while the Bag icon is present → click Bag, then ball, then Use.
  * If no target is recognized for a moment while Bag is visible → click Run.
  * “Flee” text is recognized and used to space encounter counts.

## Default config (key bits)

* Poll rate: `poll_ms = 150`
* Thresholds: `bag_threshold = 0.45`, `run_threshold = 0.45`, `ball_threshold = 0.35`, `use_threshold = 0.20`
* Regions (percent of **Roblox client area**, `L,T,R,B` in `[0..1]`):

  * `target_region = 0,0.75,0.6,1`
  * `hud_region = 0.6,0.88,0.99,1`
  * `bag_hud_region = 0,0,0.50,1`
  * `run_hud_region = 0.50,0,1,1`
  * `ball_region = 0.2,0.16,0.28,0.785`
  * `use_region = 0.35,0.785,0.44,0.825`
* Images: `bag.png`, `use.png`, `run.png` (in `assets\other\`) — replaceable if the UI changes.
* Ball choice: `use_choice = Poke Ball.png` (file name from `assets\pokeballs\`).
* Click behavior: `mouse_clicks = "2"` (double-click). Change in `settings.ini` if needed.
* Presets: three slots (`preset_1/2/3` + names) prefilled (Popular / Popular 2 / Mega Stones).

All config lives in `%APPDATA%\Astralis v1.0\settings.ini` and is editable via the Settings tab or directly in the file.

## Hotkeys

* **F6**: Pause / Resume
* **F7**: Exit application
* **F10**: Toggle the translucent **region overlay** (draws boxes over Roblox so you can tune regions)

## Tips

* If Bag/Run matching struggles, replace the templates in `assets\other\` with fresh screenshots and keep the same file names (or update the names in Settings).
* If ball selection fails, verify the **UI thumbnail** exists in `pokeballsnobg\` and the **in-game template** exists in `pokeballs\` with the same base filename.
* For OCR accuracy, keep the encounter text unobstructed and high-contrast; avoid unusual shaders/overlays.

## Troubleshooting

* **“Tesseract required” popup** → Run the included `tesseract-setup.exe` or install Tesseract from the official page.
* **“Roblox not found”** → Ensure a visible Roblox window (not minimized) is open.
* **Clicks in the wrong place** → Check `hud_region`, `bag_hud_region`, `run_hud_region`, DPI scaling.
* **Ball isn’t selected** → Ensure matching thumbnails/templates exist in `pokeballsnobg\` and `pokeballs\`.
* **OCR reads nothing** → Make sure Tesseract is installed, text is unobstructed, and adjust thresholds/regions.
* **Overlay isn’t showing** → Only visible when Roblox is partially visible. Toggle with F10.

## Uninstall / Reset

* Close the app.
* Delete `%APPDATA%\Astralis v1.0\` to remove settings, logs, and assets.
* (Optional) Delete the EXE / script folder.

## Safety & Notes

* This tool simulates mouse movement and clicks. Use at your own risk and respect the game’s Terms of Service.
* Need help? Discord: `https://discord.gg/fxwzgSDvjG`

## Credits

* OpenCV (template matching) • MSS (fast capture) • Tesseract + pytesseract (OCR) • Tkinter (UI) • NumPy (array ops)
* Tesseract OCR binaries for Windows provided by [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) (Apache License 2.0).