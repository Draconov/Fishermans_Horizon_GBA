# Fisherman's Horizon GBA

A native Game Boy Advance fishing game built with C++17 and [Butano](https://github.com/GValiente/butano).

## Build requirements

- devkitPro / devkitARM
- Butano **21.7.1**
- GNU Make
- Python 3
- `pytest` and a host C++17 compiler (`g++` or `c++`) for the lightweight project tests

## Build locally

Clone Butano next to this project and build with:

```bash
git clone --depth 1 --branch 21.7.1 https://github.com/GValiente/butano.git ../butano
make -j2 LIBBUTANO=../butano/butano
```

The ROM is written as `Fishermans_Horizon_GBA.gba`.

To create release ROM/checksum files:

```bash
python3 scripts/package_rom.py --rom Fishermans_Horizon_GBA.gba --out dist
```

## Regions

The game now supports multiple world regions through a shared region/map framework.

### Region 1 — Mari-Mari

Existing locations and progression remain intact:

- Crystal Lake
- Pier
- River
- Ocean
- Cave
- Lagoon
- Beach
- Waterfall
- Mari-Mari Shop
- Catalog
- Travel point

Current unlock items:

| Item | Price | Unlock |
| --- | ---: | --- |
| Club card | 60 | River |
| Old Boat | 30 | Ocean + Waterfall |
| Ancient Map | 120 | Cave |
| Catalog | 20 | Global Catalog |
| Captain's Hat | 60 | Lagoon |
| Beach Ball | 30 | Beach |
| **Car Keys** | **100** | **Travel between regions** |

Beach is still map-only until its own fishing background/content is added.

### Region 2 — Jarim Perla

After buying **Car Keys**, use the Travel marker on either map to move between regions.

Map 2 currently contains:

- **City Beach** — available immediately, fishing pool 8
- **Bridge** — available immediately, fishing pool 9
- **Breakwater** — fishing pool 10, unlocked by Shop 2 Item 1
- **City Shop** — completely separate inventory from Mari-Mari Shop
- **Travel** — returns to Mari-Mari

Shop 2 starts with:

| Item | Price | Effect |
| --- | ---: | --- |
| Item 1 | 20 | Unlock Breakwater |

Map 2 currently uses final-named placeholder graphics. Replace those files later with final artwork without changing gameplay code.

## Global progression

These are shared between regions:

- money
- rods and equipped rod
- bait ownership/equipped bait
- characters/current character
- sound option
- one global fish catalog

Shop 2 purchase ownership is separate from Mari-Mari Shop ownership.

## Catalog

The global catalog now contains **54 fish**:

- Mari-Mari section: fish 1–44
- Jarim Perla section: fish 45–54

Jarim Perla adds 10 species whose current visuals intentionally reuse existing fish frames until final sprites are supplied:

1. CITY MINNOW
2. GLASSFISH
3. PAVEMENT CARP
4. BRIDGE BASS
5. RUSTFIN
6. PIPE EEL
7. BREAKWATER BREAM
8. FOAMRAY
9. JETTY SHARK
10. NEON TUNA

In the Catalog, **L/R switches region sections**. D-pad navigation can also cross between the bottom row of the Mari-Mari section and the Jarim Perla section. Catalog completion requires all 54 species.

## Controls

### Title

- **A / Start** — play
- **Select** — options

### Map

- **D-pad** — move between available locations
- **A** — enter/activate the selected location
- **B** — return to title
- **L / R** — cycle owned characters
- **Start** — open the global Catalog when purchased

### Shop

- **D-pad** — move between items; page boundaries can be discovered naturally with Up/Down
- **A** — buy
- **Select** — item description
- **B** — leave / close description
- **L / R** — switch shop pages when a shop has more than one page

### Fishing

- **Hold/release A** — charge/cast and operate the rod for the current state
- **L / R while standing** — cycle owned bait
- **Select while bait is in the water** — cancel cast
- **B** — return to map when no dialog is active
- **A** — advance result/dialog text

### Catalog

- **D-pad** — move between fish
- **L / R** — switch Mari-Mari / Jarim Perla sections
- **A** — details for a caught fish
- **B** — return to map

### Options

- **A / Left / Right** — toggle sound
- **B** — return to title

## Saves

Progress is stored in GBA SRAM.

Current format:

- save image: **64 bytes**
- format: **version 3**
- payload: **32 bytes**

Version 3 stores the active region, Car Keys, 32 reserved Shop 2 ownership bits, and all 54 catalog flags. Valid **version 2 saves are migrated automatically**: existing Mari-Mari progress is preserved, Jarim Perla begins locked/unvisited, Shop 2 begins unpurchased, and fish 45–54 begin uncaught.

Loading resumes on the **last active region**. A malformed save that claims Jarim Perla without Car Keys is safely returned to Mari-Mari.

## Placeholder graphics for Map 2

These are final logical filenames even though the first implementation reuses existing art:

```text
graphics/map_bg_region2.bmp
graphics/map_travel_spots.bmp
graphics/shop_bg_region2.bmp
graphics/fishing_bg_city_beach.bmp
graphics/fishing_bg_bridge.bmp
graphics/fishing_bg_breakwater.bmp
```

Every bitmap has a matching Butano JSON file. Final artwork can replace these assets directly.

Fishing backgrounds use the established **256×768, 8-bit indexed BMP** format: three stacked 256×256 frames.

## Tests

The repository intentionally keeps only two test source files:

```text
tests/runtime_tests.cpp
tests/test_project.py
```

Run everything with:

```bash
python3 -m pytest -q tests/test_project.py
```

The suite compiles/runs the host C++ runtime contract, validates graphics/JSON pairing and generated-item references, checks the standalone repo layout, and verifies ROM packaging. It does not enforce artwork pixels.

The real Butano/devkitARM ROM build remains the final integration gate.

## GitHub Actions and releases

`.github/workflows/gba.yml` uses the pinned `devkitpro/devkitarm:20260221` container and Butano **21.7.1**. A normal build performs the project tests, real Butano ROM build, package/checksum verification, and artifact upload.
