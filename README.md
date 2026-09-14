# Fishermans_Horizon_GBA

Native Game Boy Advance reconstruction of **Fisherman's Horizon 1.1**, using the supplied Android APK as behavioral and asset evidence. The GBA program is original C++ code; it does not emulate Android, Java, Dalvik, Canvas, MediaPlayer, or SoundPool.

## M0 status

M0 freezes the reference APK, provides a reproducible DEX/symbol recovery harness, stages the title artwork into a GBA-friendly background, and provides the first Butano boot/title source skeleton.

The compatibility target is **Butano 21.7.1** with devkitARM/devkitPro. The project Makefile follows the current Butano template shape and accepts `LIBBUTANO` as an override.

## M1 status

M1 adds the first returning-save vertical slice: the recovered animated title sea strip, native GBA title controls, the original map background and marker animation, D-pad map selection, and entry into the exact Crystal Lake background. The reference-derived 240x160 backgrounds remain unscaled and are center-padded for Butano.

The original **fresh-save** path is not bypassed: `Play` with an incomplete prologue routes to the recovered `Event` state, which remains a later dialogue milestone. M1 runs the returning-save fixture so `A` can reach the map while that event system is still absent. On the map, only Crystal Lake is dispatched by `A`; Pier, Shop, and later unlocks are preserved in the recovered flow model but are not replaced with fake scenes.

M1 does **not** implement fishing mechanics yet. Crystal Lake is a visual entry checkpoint with `B` returning to the map. Audio is likewise evidence-only in this milestone; no MP3 playback parity is claimed.

## M2 status

M2 replaces that placeholder with the first complete **Crystal Lake fishing loop**. The state machine is a platform-neutral C++ model backed by exact DEX method fingerprints and recovered data: charge/cast timing, bait movement and lure checks, fish selection, hook/recoil, tension and stamina, catch or line break, reward timing, the 999-money cap, and catalog mutation. Crystal Lake preserves the original random table where roll `0` catches nothing and rolls `1..9` select its nine recovered fish.

The GBA input adaptation is intentionally small: **A = hold/release rod**, **Select = cycle owned bait**, **B = Back** only when the fishing state allows it, and A dismisses result dialogs. Presentation uses the original 240x160 Crystal Lake pixels with its recovered three-frame sea strip composited into one GBA-safe 8bpp background. Fishing sprites are split into independent 4bpp banks so they do not fight over the GBA OBJ palette.

M2 does not claim the original dialog typography or audio yet. Result-dialog ownership/timing is implemented, but the full original text rendering and MP3/SFX conversion remain later presentation milestones.

## M3 status

M3 expands the M2 fishing core to **all five fishing areas**: Crystal Lake, Pier, River, Ocean, and Cave. The content layer is recovered directly from `FishingArea.loadArea()`/`lurePool()` and now carries all 45 pool constructor instances representing **44 unique catalog fish**, including the original cross-pool SIRIRIDINE duplicate and Cave's literal `???` fish. River, Ocean, and Cave remain controlled by their recovered unlock flags; Pier is available by default.

The renderer now uses five native 240x160 backgrounds with the recovered three-frame sea strip, two deterministic 4bpp banks containing every fish sprite, and **three rod variants** with all 36 recovered animation frames. No M0/M1/M2 graphics were resampled or rewritten to make this fit.

M3 also recovers the original fishing SFX channel mapping and emits **semantic sound events** at the recovered gameplay boundaries (bait page, throw, water, hook, reel/coil, line break, fanfare, and coin). Actual GBA **sample conversion/playback** remains an M5 audio task; M3 preserves when each cue happens without pretending MP3 playback parity exists yet.

## M4 status

M4 adds the original progression and presentation screens on top of the complete fishing content: **16 one-time shop items** with recovered prices/effects, the original **44-entry catalog** ordering and completion trigger, Options state, and the two story events. A genuine **fresh-save** path now goes from Title into the **Cecil prologue** instead of using the old returning-save bootstrap shortcut. Cid and Fran remain baseline characters; Leon, Sazh, Rosa, and Shadow are unlocked by their recovered shop purchases and render with their original 16-pose character sheets.

Shop, Catalog, Options, and Event now have native GBA scenes built from the original APK artwork and the recovered 8x8 font mapping. Catalog completion still triggers the original ending-event lifecycle. M4 intentionally does **not** claim persistent GBA save-data compatibility or final audio sample playback; those remain later milestones.

## Reference APK

The reference APK is not committed to this repository. For private development, point the tools at the original `fishermans-horizon-1-1.apk` supplied by the developer/user.

Canonical SHA-256:

`581aeb20073592905b5a82ddc38a54f522f2f369330ae92f025ae7d52ca0d137`

Verify and stage the M0 title asset:

```bash
python scripts/check_reference.py /path/to/fishermans-horizon-1-1.apk
python scripts/stage_reference_assets.py /path/to/fishermans-horizon-1-1.apk
```

The source title is 240x160. Butano regular backgrounds use 256-based canvases, so the staging tool center-pads it to 256x256 at `(8,48)` without scaling any source pixel. The GBA's centered 240x160 viewport therefore sees the original image pixel-for-pixel.

## Host tests

```bash
FH_REFERENCE_APK=/path/to/fishermans-horizon-1-1.apk pytest -q
```

These tests do not require devkitARM or an emulator.

## GBA build

Install devkitARM/devkitPro and obtain **Butano 21.7.1**. If the Butano checkout is a sibling directory with its library at `../butano/butano`, build with:

```bash
make -j4
```

For another location:

```bash
make -j4 LIBBUTANO=/absolute/path/to/butano/butano
```

A successful toolchain build produces `Fishermans_Horizon_GBA.gba`.

## Project boundaries

`reference/` stores hashes, inventories and recovered machine-readable metadata. `tools/` and `scripts/` reproduce that evidence. `src/` and `include/` are the native GBA implementation. `graphics/title.bmp` is reference-derived material staged for private parity work.

Public distribution of the original game's artwork, music, text, or a ROM containing those assets should wait for permission or another clear legal basis. Keeping the reference APK outside the repository makes that boundary explicit.

## One-command M0 verification

Run the complete M0 gate with:

```bash
python scripts/verify_m0.py --apk /path/to/fishermans-horizon-1-1.apk
```

The command rechecks the frozen APK, regenerates and compares the recovered DEX surface, regenerates and compares the title asset, runs the full host test suite, and builds the ROM only when both devkitARM and the configured Butano checkout are available. A missing local ARM toolchain is reported explicitly and is never presented as a successful ROM build.

## One-command M1 verification

Run the M1 gate with:

```bash
python scripts/verify_m1.py --apk /path/to/fishermans-horizon-1-1.apk
```

It rechecks the canonical APK and M0 evidence, regenerates and byte-compares the M1 title/map facts and staged graphics, runs the full host suite, and attempts a ROM build only when devkitARM and Butano are actually available. Missing build dependencies are reported as `INFO`, never as a successful ROM build.

## One-command M2 verification

Run the M2 gate with:

```bash
python scripts/verify_m2.py --apk /path/to/fishermans-horizon-1-1.apk
```

It rechecks the full M0/M1 reference gate, regenerates and byte-compares the M2 fishing facts and every M2 fishing asset, runs the entire host suite, and attempts the GBA build only when devkitARM and Butano are really available. A missing local ARM toolchain remains an explicit `INFO` condition rather than a fake build pass.

## One-command M3 verification

Run the M3 gate with:

```bash
python scripts/verify_m3.py --apk /path/to/fishermans-horizon-1-1.apk
```

It rechecks the canonical APK and the complete M0-M2 deterministic gate, regenerates and byte-compares the full M3 fishing-content evidence and all M3 area/fish/rod assets, runs the complete host suite, and attempts the ROM build only when devkitARM and Butano are actually present. Missing build dependencies remain an explicit `INFO` condition rather than a fake ROM success.
## One-command M4 verification

Run the M4 gate with:

```bash
python scripts/verify_m4.py --apk /path/to/fishermans-horizon-1-1.apk
```

It rechecks the canonical APK and complete M0-M3 deterministic gate, regenerates and byte-compares the M4 progression evidence and every M4 Shop/Catalog/Options/Event/character asset, runs the full host suite, and attempts the ROM build only when devkitARM and Butano are actually present. Missing build dependencies remain an explicit `INFO` condition rather than a fake ROM success.


## M5 status

M5 adds persistent saves, original sampled audio, and release-facing presentation/resource hardening. Progression is encoded in a deterministic **32-byte** versioned save image with `FHGS` magic, payload length and CRC32, then stored through Butano **SRAM**. Corrupt or unsupported saves fall back to the canonical fresh-save defaults, and SRAM writes occur only when persistent progression changes.

The 13 audio files actually present in the reference APK are recovered and deterministically converted to mono unsigned 8-bit PCM WAV at **16 kHz**, matching Butano 21.7.1's default Direct Sound mixing rate. The original Shop reference to missing `textSE.mp3` is recorded as an APK anomaly and is not fabricated. Scene music and one-shot cues are routed through a single `AudioManager`; the sound option mutes both music and effects, and fishing inherits the map track as in the recovered source behavior.

M5 also validates GBA sprite dimensions, 4bpp palette indexes, scene OAM upper bounds, and visible 240x160 background composition against the canonical APK. This pass corrected the right-hand rod strip from an illegal 16x64 OBJ into two lossless 16x32 OBJs. Run the complete checkpoint with:

```bash
python scripts/verify_m5.py --apk /path/to/fishermans-horizon-1-1.apk
```

As with earlier gates, ROM compilation is reported separately: it is only marked PASS when devkitARM and the pinned Butano checkout are actually available.

## M6 release hardening

The GitHub release pipeline lives in `.github/workflows/gba.yml`. It builds with the pinned `devkitpro/devkitarm:20260221` image (the r67-era image required by the M8 toolchain contract) and Butano `21.7.1`, runs only the self-contained GBA project tests, validates the pinned toolchain, compiles the ROM, packages it with `scripts/package_rom.py`, verifies its SHA-256, and performs a bounded mGBA boot smoke test. **Release CI never reads, downloads, or requires the original Android APK and does not run any APK/reference/recovery parity tests.** Those recovery tests remain local reverse-engineering tools only. Every successful workflow run uploads a downloadable `gba-rom` artifact containing exactly `Fishermans_Horizon_GBA.gba` and `Fishermans_Horizon_GBA.gba.sha256`.

A tag beginning with `v` automatically builds and publishes a GitHub Release. For example:

```bash
git tag v0.8.0
git push origin v0.8.0
```

You can also open **Actions -> Build and release GBA ROM -> Run workflow**. Leave `release_tag` blank to build only the downloadable `gba-rom` artifact, or enter a tag such as `v0.8.0` to create/update that GitHub Release after the ROM passes all checks. The build job remains read-only; only the release job receives `contents: write` permission. Do not publicly distribute reference-derived assets or a ROM containing them unless you have the necessary permission or another clear legal basis.

Run the complete local M6 gate with:

```bash
python scripts/verify_m6.py --apk /path/to/fishermans-horizon-1-1.apk
```

The local M6 gate can still be used when doing reverse-engineering work with a privately supplied reference APK. That is separate from release CI. GitHub Release CI uses only the self-contained project-test allowlist, then requires the pinned build container to complete the real ROM build, deterministic package/checksum validation, and mGBA smoke test before a release can run.

## M7 final parity

M7 closes the remaining source-level parity gaps found after M6. Cold boot now runs the recovered original `GameIntro`; Cecil/ending and fishing catch/line-break presentation use a shared recovered `DialogBox`; reachable `ScreenFlash` fades and the pale-green line-break flash are adapted through GBA palette fading; and the obsolete Android image mode is removed completely. The GBA port now has one native 240x160 presentation path only.

M7 deliberately changes the save schema to version 2. M5/M6 GBA saves are not migrated and are rejected as unsupported, falling back to the canonical fresh-save defaults as approved for this milestone.

Run the complete source-level parity gate with:

```bash
python scripts/verify_m7.py --apk /path/to/fishermans-horizon-1-1.apk
```

The gate rechecks the M0-M6 deterministic source/release contracts, regenerates the M7 DEX evidence and M7-only assets byte-for-byte, rejects any reintroduced image-mode runtime API/state, runs the host suite once, and attempts a ROM build only when devkitARM and Butano are really available. Real ROM bring-up and emulator/hardware validation remain the separate M8 milestone.

## M8 local toolchain inspection

M8 adds `scripts/bootstrap_m8_toolchain.py` to validate an installed local GBA toolchain before attempting the first ROM build. The build is pinned to **devkitARM r67 / GCC 15.2.0** and **Butano 21.7.1 at commit `112a1827c9c6d9e6041a7e93e66f04c4561a6415`**. The helper rejects any other compiler version, Butano tag, or Butano commit and records the validated release/version paths in its JSON report. Installation remains external so CI/local machines cannot silently drift to a different SDK.

Example after installing devkitPro and cloning Butano 21.7.1:

```bash
python scripts/bootstrap_m8_toolchain.py \
  --devkitpro /opt/devkitpro \
  --butano ../butano/butano \
  --json reference/m8_toolchain_report.json
```
