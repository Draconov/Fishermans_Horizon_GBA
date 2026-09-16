# Fisherman's Horizon GBA

A native Game Boy Advance fishing game built with C++17 and [Butano](https://github.com/GValiente/butano).

## Build requirements

- devkitPro / devkitARM
- Butano **21.7.1**
- GNU Make
- Python 3 for tests and release packaging
- `pytest` and a host C++17 compiler (`g++` or `c++`) for the lightweight project tests

## Build locally

Clone Butano next to this project and build with:

```bash
git clone --depth 1 --branch 21.7.1 https://github.com/GValiente/butano.git ../butano
make -j2 LIBBUTANO=../butano/butano
```

The ROM is written as:

```text
Fishermans_Horizon_GBA.gba
```

To create the release ROM and checksum files:

```bash
python3 scripts/package_rom.py --rom Fishermans_Horizon_GBA.gba --out dist
```

## Controls

### Title

- **A / Start** — play
- **Select** — options

### Map

- **D-pad** — move between available locations
- **A** — enter the selected location
- **B** — return to the title screen
- **L / R** — cycle owned characters
- **Start** — open the Catalog when it has been purchased

### Shop

- **D-pad** — move between items
- **A** — buy the selected item
- **Select** — read the item description
- **B** — leave the shop; while a description is open, close it
- **L / R** — switch shop pages

The shop contains the original 16-item page plus a second page containing Captain's Hat and Beach Ball.

### Fishing

- **Hold/release A** — charge and cast / operate the rod according to the current fishing state
- **L / R while standing** — cycle through owned bait
- **Select while bait is in the water** — cancel the cast
- **B** — return to the map when no dialog is active
- **A** — advance result/dialog text

### Catalog

- **D-pad** — move between entries
- **A** — open details for a caught fish
- **B** — return to the map

### Options

- **A / Left / Right** — toggle sound
- **B** — return to the title screen

## Locations and unlocks

Always available:

- Crystal Lake
- Pier
- Mari-Mari Shop

Shop progression:

| Item | Price | Unlock |
| --- | ---: | --- |
| Club card | 60 | River |
| Old Boat | 30 | Ocean **and Waterfall** |
| Ancient Map | 120 | Cave |
| Catalog | 20 | Catalog |
| Captain's Hat | 60 | Lagoon |
| Beach Ball | 30 | Beach |

**Lagoon** is playable as fishing pool 6. **Beach** and **Waterfall** currently appear on the map after they are unlocked but do not enter a fishing scene yet.

## Saves

Progress is stored in GBA SRAM. The current save image is **32 bytes**, format **version 2**, with a **19-byte payload**. Existing version-2 saves remain compatible with the current shop and location unlock flags.

The game saves when progress changes and restores the saved state on startup.

## Graphics and assets

Graphics live in `graphics/`. Every active bitmap has a matching Butano JSON configuration with the same stem, for example:

```text
graphics/shop_bg.bmp
graphics/shop_bg.json
```

Current artwork is 8-bit indexed BMP data prepared for Butano. Asset filenames describe their runtime purpose (`shop_bg`, `fishing_bg_lagoon`, `dialog_panel`, `ui_font`, and so on) rather than development milestones.

Artwork can change freely as long as the asset remains valid for the build. The test suite checks asset structure and generated-item integration; it does **not** enforce exact artwork pixels.

## Tests

The repository intentionally keeps only two test source files:

```text
tests/runtime_tests.cpp
tests/test_project.py
```

Run all project tests with:

```bash
python3 -m pytest -q tests/test_project.py
```

`test_project.py` compiles and executes the single host-side C++ runtime contract, validates graphics/JSON pairing and generated asset references, checks the standalone repository layout, and verifies ROM packaging.

The real Butano ROM build remains the final integration check.

## GitHub Actions and releases

`.github/workflows/gba.yml` uses the pinned `devkitpro/devkitarm:20260221` container and Butano **21.7.1**. A build run performs:

1. the two-file project test suite;
2. a real Butano/devkitARM ROM build;
3. ROM packaging and SHA-256 verification;
4. artifact upload;
5. optional GitHub Release publication for tags or an explicitly supplied release tag.

The release artifact contains only:

```text
Fishermans_Horizon_GBA.gba
Fishermans_Horizon_GBA.gba.sha256
```
