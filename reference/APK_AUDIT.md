# Reference APK audit

Reference file: `fishermans-horizon-1-1.apk`
SHA-256: `581aeb20073592905b5a82ddc38a54f522f2f369330ae92f025ae7d52ca0d137`
Size: 1,133,461 bytes
APK entries: 39
DEX size: 86,008 bytes
DEX class definitions: 29
DEX strings: 1,039
DEX types: 78
DEX method IDs: 253
Native libraries: none observed
Package: `com.fishermanshorizon.app`
Entry activity string: `com.fishermanshorizon.app.StartActivity`

## Primary graphics

| Asset | Dimensions | Observed RGBA colors |
|---|---:|---:|
| catalog.png | 240x160 | 14 |
| cave.png | 240x160 | 14 |
| crystalLake.png | 240x160 | 18 |
| crystalLakeNoHud.png | 240x160 | 17 |
| map.png | 240x160 | 18 |
| ocean.png | 240x160 | 14 |
| options.png | 240x160 | 9 |
| pier.png | 240x160 | 20 |
| river.png | 240x160 | 17 |
| shop.png | 240x160 | 19 |
| title.png | 240x160 | 10 |
| charSpriteSheet.png | 256x480 | 18 |
| seaTiles.png | 240x16 | 4 |
| stickSpriteSheet.png | 320x576 | 11 |
| tiles.png | 128x304 | 20 |

`introCredit.png` is 144x64 with 2 observed RGBA colors.

## Audio

All reference audio is MP3, 44.1 kHz stereo.

| Asset | Approx duration |
|---|---:|
| music/title.mp3 | 41.195 s |
| music/welcome.mp3 | 6.896 s |
| music/mari_mari.mp3 | 3.474 s |
| music/select.mp3 | 3.474 s |
| SE/coilSE.mp3 | 0.261 s |
| SE/coinSE.mp3 | 1.750 s |
| SE/fanfareSE.mp3 | 0.470 s |
| SE/fishCatchBaitSE.mp3 | 1.750 s |
| SE/introSE.mp3 | 0.888 s |
| SE/lineBreakSE.mp3 | 1.750 s |
| SE/nextPageSE.mp3 | 0.183 s |
| SE/throwSE.mp3 | 1.750 s |
| SE/waterSE.mp3 | 1.750 s |

## Recovered class surface

Key gameplay classes and selected methods visible from the DEX method table:

- `Framework`: `init`, `update`, `draw`, `setMoney`
- `GameTitle`: `init`, `update`, `draw`, `loadAssets`, `exit`, `seaImage`
- `GameMap`: `init`, `update`, `draw`, `loadAssets`, `setSprite`, `spriteChanger`, `exit`
- `GameFishing`: `stateInit`, `stateStand`, `stateGetReadyToThrow`, `stateThrow`, `stateBaitInWater`, `stateFishInLine`, `stateRecoil`, `stateFishCatch`, `stateLineBreak`, `stateReward`, plus `checkNextBait`, `setEquipedBait`, `setDelay`
- `GameShop`: `checkMoney`, `itemChecker`, `itemGetter`, `itemSetter`, `talkAnimation`
- `GameCatalog`: `setFish`, `ending`
- `FishingArea`: `loadArea`, `lurePool`, `inLinePool`, `addCatalog`
- `Fish`: `lure`, `inLine`
- `Bait`: `lure`, `set`
- `GlobalVar`: `loadData`, `saveData`, `convertMoney`
- `DialogBox`: `newText`, `setNewPage`, `getChar`, `update`, `draw`
- `ScreenFlash`: `init`, `update`, `draw`
- `SoundEngine`: `loadMusic`, `loadSE`, `playMusic`, `fadeoutMusic`

## Recovered content shape

- 44 fish/catalog slots: `fish00` ... `fish2B`.
- 16 shop item positions: `0` ... `F`.
- Fishing locations named by `FishingArea`: Crystal Lake, Pier, River, Ocean, Cave.
- Fishing state symbols: `INIT`, `STAND`, `GET_READY_TO_THROW`, `THROW`, `BAIT_IN_WATER`, `FISH_IN_LINE`, `RECOIL`, `FISH_CATCH`, `LINE_BREAK`, `REWARD`.
- Visible progression/global fields include money digits, current character, current rod, bait ownership, rod ownership, club card, ancient map, old boat, catalog/fish flags, prologue, sound, and image/scaling option.

This audit intentionally records only information directly observed from the supplied APK bytes. Exact constants, timings, prices, probabilities, touch rectangles, save layout, and state transition logic still require DEX instruction-level recovery.
