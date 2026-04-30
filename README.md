Version: 3.0  
Created by Bloxables  

**License:** Source-available. Personal use and local modification allowed. Redistribution prohibited. See `LICENSE.txt`.

## Overview

Astralis is a Windows-only helper for Roblox that:

* reads on-screen text (OCR) in a small “target” area,
* decides whether the encounter matches your enabled items or Pokémon,
* if it matches: opens **Bag → Pokéballs**, selects your chosen ball, and hits **Use**,
* if it doesn’t: clicks **Run**.

Everything is configurable (regions, thresholds, items, Pokémon, presets), and the app includes overlays, logs, and global hotkeys.

## What’s new in this version (revamped logic)

* **OCR-based detection**: Uses Tesseract via `pytesseract` on a targeted region to read encounter names. Fuzzy matching handles typos/variants.
* **Smarter encounter flow**:
  * Detects the Bag icon appearing (rising edge) to mark a new encounter.
  * Caches text seen **before** the Bag and **during** the encounter.
  * Supports both **item matching** and **Pokémon matching**.
  * If matched → open Bag, select ball, press Use. If not matched → auto **Run**.
* **Improved capture detection**:
  * Detects “Gotcha!” / “added to box” text to confirm successful capture.
  * Reduces reliance on fallback encounter detection.
* **Two overlays**:
  * **Status overlay** (auto-hides if Roblox isn’t visible)
  * **Region overlay** (F10): visualizes all detection regions
* **Global hotkeys** (work while unfocused):  
  F6 = Pause/Resume • F7 = Exit • F10 = Toggle region overlay
* **Logs + stats**:
  * Encounter logs (items + Pokémon)
  * Debug logs (OCR + actions)
  * Counters for encounters and captures
* **Improved config UX**:
  * Settings UI with live syncing
  * Find tab supports item + Pokémon filters

## Requirements

* Windows 10/11 (64-bit)
* Roblox desktop client
* **Tesseract OCR 5+**

Default path:
`C:\Program Files\Tesseract-OCR\tesseract.exe`

Astralis will auto-detect Tesseract if installed.

---

## Installation

**Prebuilt EXE:**

1. Run the installer (`Astralis-Setup-x.x.x.exe`)
2. Launch Astralis
3. Assets and config are automatically created in `%APPDATA%\Astralis\`

**No manual asset setup is required anymore.**

---

## Data & Folders

All runtime data lives under:

* `%APPDATA%\Astralis\`
* `settings.ini`
* `assets\` (auto-downloaded or seeded)

Older `Astralis vX.Y` folders are cleaned automatically.

---

## UI at a glance

* **Find tab**
  * Enable **items** and/or **Pokémon**
  * Supports amounts and filtering

* **Use tab**
  * Select preferred Pokéball

* **Logs tab**
  * Encounter + debug logs

* **Settings tab**
  * Regions, thresholds, behavior

---

## Quick start

1. Open Roblox and start encounters
2. Launch Astralis
3. Configure:
   - Find → select targets
   - Use → select ball
4. Click **Start**

Hotkeys:
F6 = Pause • F7 = Exit • F10 = Overlay

---

## How detection works (high level)

* OCR reads encounter text from the target region
* Text is normalized and matched against enabled targets
* Bag/Run buttons are detected via template matching

Flow:

* Match found → Bag → Ball → Use  
* No match → Run  

---

## Default config (key bits)

* Poll rate: `poll_ms ≈ 50`
* Thresholds tuned for stability (bag/run/ball detection)
* Regions defined as percentages of the Roblox window

All config lives in `%APPDATA%\Astralis\settings.ini`

---

## Hotkeys

* F6: Pause / Resume  
* F7: Exit  
* F10: Toggle region overlay  

---

## Tips

* Keep encounter text unobstructed for best OCR accuracy
* If clicking fails, adjust regions or thresholds
* If OCR struggles, tweak target region or contrast

---

## Troubleshooting

* **Tesseract missing** → Install Tesseract
* **Clicks wrong** → Check regions / DPI scaling
* **OCR fails** → Adjust region / ensure text visible
* **Ball not selected** → Verify ball exists in UI

---

## Uninstall / Reset

* Delete `%APPDATA%\Astralis\`
* Remove app install

---

## Safety & Notes

* Simulates mouse input
* Use at your own risk

---

## Support Development

If you’d like to support Astralis and get access to perks like early update testing, you can do so here:  
👉 [Buy Me a Coffee](https://buymeacoffee.com/astralissoftware)