from __future__ import annotations

from pathlib import Path
import json
import struct


def test_makefile_declares_butano_project():
    text = Path("Makefile").read_text(encoding="utf-8")
    assert "TARGET := Fishermans_Horizon_GBA" in text
    assert "LIBBUTANO ?=" in text
    assert "GRAPHICS := graphics" in text
    assert "ROMTITLE := FISH HORIZON" in text
    assert "ROMCODE := FHGA" in text
    assert "include $(LIBBUTANOABS)/butano.mak" in text


def test_main_is_native_butano_only():
    text = Path("src/main.cpp").read_text(encoding="utf-8")
    assert '#include "bn_core.h"' in text
    assert '#include "app.h"' in text
    assert "bn::core::init()" in text
    assert "bn::core::update()" in text
    assert "fh::App app" in text
    assert "app.update()" in text
    assert "fh::TitleScene" not in text

    all_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in list(Path("src").glob("*.cpp")) + list(Path("include").glob("*.h"))
    ).lower()
    forbidden = ("android", "dalvik", "jni", "mediaplayer", "soundpool", "java/")
    assert not any(token in all_source for token in forbidden)


def test_game_state_starts_at_intro():
    header = Path("include/game_state.h").read_text(encoding="utf-8")
    source = Path("src/game_state.cpp").read_text(encoding="utf-8")
    assert "enum class GameState" in header
    assert "Title" in header
    assert "GameState initial_game_state()" in source
    assert "return GameState::Intro;" in source


def test_title_scene_uses_safe_single_map_animation_frames():
    text = Path("src/title_scene.cpp").read_text(encoding="utf-8")
    assert '#include "bn_regular_bg_items_title_anim.h"' not in text
    assert '#include "bn_regular_bg_items_title_frame_112.h"' in text
    assert '#include "bn_regular_bg_items_title_frame_113.h"' in text
    assert '#include "bn_regular_bg_items_title_frame_114.h"' in text
    assert '#include "bn_keypad.h"' in text
    assert "bn::regular_bg_items::title_frame_112.create_bg(0, 0)" in text
    assert "bn::keypad::a_pressed()" in text
    assert "bn::keypad::start_pressed()" in text
    assert "set_map" not in text


def test_title_asset_is_butano_regular_background():
    assert Path("graphics/title.bmp").is_file()
    metadata = Path("graphics/title.json").read_text(encoding="utf-8")
    assert '"type": "regular_bg"' in metadata
    assert '"bpp_mode": "bpp_8"' in metadata


def test_readme_pins_butano_and_explains_private_reference_asset():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "Butano 21.7.1" in text
    assert "reference APK is not committed" in text
    assert "private development" in text


def test_m3_map_scene_exposes_all_recovered_fishing_markers_and_routes():
    header = Path("include/map_scene.h").read_text(encoding="utf-8")
    source = Path("src/map_scene.cpp").read_text(encoding="utf-8")
    assert "class MapScene" in header
    assert '#include "bn_regular_bg_items_map.h"' in source
    assert '#include "bn_sprite_items_map_spots.h"' in source
    assert "create_sprite(-16, -60, 2)" in source  # Shop
    assert "create_sprite(32, -52, 0)" in source   # Crystal Lake
    assert "create_sprite(16, 4, 0)" in source     # Pier
    assert "create_sprite(96, -60, 0)" in source   # River
    assert "create_sprite(-8, 52, 0)" in source    # Ocean
    assert "create_sprite(-96, 20, 0)" in source   # Cave
    for member in ("_river_spot", "_ocean_spot", "_cave_spot"):
        assert member in header
    assert "map_target_enabled(MapTarget::River)" in source
    assert "map_target_enabled(MapTarget::Ocean)" in source
    assert "map_target_enabled(MapTarget::Cave)" in source
    assert "M1 only dispatches Crystal Lake" not in source
    assert "flow.handle_map_command(MapCommand::Confirm)" in source

def test_m2_fishing_scene_is_thin_adapter_over_fishing_model():
    header = Path("include/fishing_scene.h").read_text(encoding="utf-8")
    source = Path("src/fishing_scene.cpp").read_text(encoding="utf-8")
    app = Path("src/app.cpp").read_text(encoding="utf-8")

    assert '#include "fishing_model.h"' in header
    assert '#include "bn_random.h"' in header
    assert "FishingModel _model" in header
    assert "bn::random _random" in header
    assert "bn::vector<bn::sprite_ptr, 32> _line_dots" in header

    for include in (
        'bn_regular_bg_items_fishing_area_crystal.h',
        'bn_regular_bg_items_fishing_area_pier.h',
        'bn_regular_bg_items_fishing_area_river.h',
        'bn_regular_bg_items_fishing_area_ocean.h',
        'bn_regular_bg_items_fishing_area_cave.h',
        'bn_sprite_items_fishing_char.h',
        'bn_sprite_items_fishing_rods_left.h',
        'bn_sprite_items_fishing_rods_right.h',
        'bn_sprite_items_fishing_bait.h',
        'bn_sprite_items_fishing_fish_m3_0.h',
        'bn_sprite_items_fishing_fish_m3_1.h',
        'bn_sprite_items_fishing_splash.h',
        'bn_sprite_items_fishing_coin.h',
        'bn_sprite_items_fishing_hud.h',
        'bn_sprite_items_fishing_meter.h',
        'bn_sprite_items_fishing_line_dot.h',
    ):
        assert f'#include "{include}"' in source

    assert "bn::keypad::a_held()" in source
    assert "bn::keypad::a_pressed()" in source
    assert "bn::keypad::select_pressed()" in source
    assert "bn::keypad::b_pressed()" in source
    assert "_model.needs_random_roll() ? _random.get_int(10) : 0" in source
    assert "flow.cycle_owned_bait()" in source
    assert "_model.set_equipped_bait" in source
    assert "flow.apply_fishing_reward" in source
    assert "flow.handle_fishing_back" in source
    assert "set_fishing_background_map(_background, _pool, map_index)" in source
    assert "flow.apply_fishing_reward(reward.fish_number, reward.amount)" in source

    # Gameplay constants live in FishingModel, not in presentation/input glue.
    for forbidden in ("280", "999", "1200", "critical_stamina"):
        assert forbidden not in source

    assert "FishingScene(int pool, int rod_index, int equipped_bait, int character_index)" in header
    assert "_flow.current_character()" in app
    assert "_flow.fishing_pool() >= 1" in app
    assert "_flow.fishing_pool() <= 5" in app


def test_m2_generated_fishing_assets_are_declared_for_butano():
    stems = (
        "fishing_lake", "fishing_char", "fishing_rod_left", "fishing_rod_right",
        "fishing_bait", "fishing_fish_a", "fishing_fish_b", "fishing_splash",
        "fishing_coin", "fishing_hud", "fishing_meter", "fishing_line_dot",
    )
    for stem in stems:
        assert Path(f"graphics/{stem}.bmp").is_file()
        assert Path(f"graphics/{stem}.json").is_file()

    assert not Path("graphics/fishing_sea.bmp").exists()
    assert not Path("graphics/fishing_bait_fish.bmp").exists()


def test_app_owns_flow_model_and_only_active_scene_resources():
    header = Path("include/app.h").read_text(encoding="utf-8")
    source = Path("src/app.cpp").read_text(encoding="utf-8")
    assert "class App" in header
    assert "FlowModel _flow" in header
    assert "bn::optional<TitleScene>" in header
    assert "bn::optional<MapScene>" in header
    assert "bn::optional<FishingScene>" in header
    assert "_title_scene.reset()" in source
    assert "_map_scene.reset()" in source
    assert "_fishing_scene.reset()" in source
    assert "_flow(SaveStorage::load())" in source
    assert "progress.prologue_complete = true" not in source


def test_m1_generated_assets_are_declared_for_butano():
    for stem in ("title_anim", "title_frame_112", "title_frame_113", "title_frame_114", "map", "map_spots", "crystal_lake"):
        assert Path(f"graphics/{stem}.bmp").is_file()
        assert Path(f"graphics/{stem}.json").is_file()


def test_m3_fishing_scene_uses_generic_area_fish_and_rod_assets():
    header = Path("include/fishing_scene.h").read_text(encoding="utf-8")
    source = Path("src/fishing_scene.cpp").read_text(encoding="utf-8")

    for stem in (
        "fishing_area_crystal", "fishing_area_pier", "fishing_area_river",
        "fishing_area_ocean", "fishing_area_cave",
    ):
        assert f'#include "bn_regular_bg_items_{stem}.h"' in source
    for stem in ("fishing_fish_m3_0", "fishing_fish_m3_1", "fishing_rods_left", "fishing_rods_right"):
        assert f'#include "bn_sprite_items_{stem}.h"' in source

    assert "create_fishing_background" in source
    assert "set_fishing_background_map" in source
    assert "m3_fish_bank" in source
    assert "m3_fish_frame" in source
    assert "_model.rod_index() * 12 + _model.stick_frame()" in source
    assert "_rod_right_top" in header and "_rod_right_bottom" in header
    assert "rod_frame * 2" in source and "rod_frame * 2 + 1" in source
    assert "AudioCue take_audio_event() noexcept" in header
    assert "AudioCue _audio_event = AudioCue::None" in header
    assert "audio_cue_from_fishing(_model.take_sound_event())" in source



def test_m5_scene_audio_cue_members_are_declared():
    for stem in ("title", "map", "fishing", "shop", "catalog", "options", "event"):
        header = Path(f"include/{stem}_scene.h").read_text(encoding="utf-8")
        source = Path(f"src/{stem}_scene.cpp").read_text(encoding="utf-8")
        assert "AudioCue take_audio_event() noexcept" in header
        assert "AudioCue _audio_event = AudioCue::None" in header
        assert "_audio_event" in source


def test_m4_progression_scenes_are_real_model_backed_routes():
    app_h = Path("include/app.h").read_text(encoding="utf-8")
    app_cpp = Path("src/app.cpp").read_text(encoding="utf-8")
    for scene in ("ShopScene", "CatalogScene", "OptionsScene", "EventScene"):
        assert f"bn::optional<{scene}>" in app_h
    for state in ("Shop", "Catalog", "Options", "Event"):
        assert f"case GameState::{state}:" in app_cpp

    shop = Path("src/shop_scene.cpp").read_text(encoding="utf-8")
    assert '#include "shop_model.h"' in shop
    assert '#include "bn_regular_bg_items_m4_shop.h"' in shop
    assert "bn::keypad::a_pressed()" in shop
    assert "bn::keypad::b_pressed()" in shop
    assert "purchase(flow)" in shop

    catalog = Path("src/catalog_scene.cpp").read_text(encoding="utf-8")
    assert '#include "catalog_model.h"' in catalog
    assert '#include "bn_regular_bg_items_m4_catalog_anim.h"' in catalog
    assert "selected_caught(flow)" in catalog
    assert "handle_catalog_back(_model.complete(flow))" in catalog

    options = Path("src/options_scene.cpp").read_text(encoding="utf-8")
    assert '#include "options_model.h"' in options
    assert '#include "bn_regular_bg_items_m7_options_anim.h"' in options
    assert "toggle_sound(flow)" in options
    assert "cycle_image(flow)" not in options
    assert "stretched" not in options
    assert "half" not in options
    assert "back(flow)" in options

    map_source = Path("src/map_scene.cpp").read_text(encoding="utf-8")
    assert "case MapTarget::Shop:" in map_source
    assert "case MapTarget::Catalog:" in map_source
    assert "flow.handle_map_command(MapCommand::Confirm);" in map_source
    assert "m1_returning_progress" not in app_cpp
    assert "progress.prologue_complete = true" not in app_cpp

    fishing = Path("src/fishing_scene.cpp").read_text(encoding="utf-8")
    for character in range(6):
        assert f'#include "bn_sprite_items_fishing_char_m4_{character}.h"' in fishing
    assert "create_character_sprite" in fishing
    assert "_flow.current_character()" in app_cpp
    assert "cycle_owned_character(-1)" in map_source
    assert "cycle_owned_character(1)" in map_source

    event = Path("src/event_scene.cpp").read_text(encoding="utf-8")
    assert '#include "event_model.h"' in event
    assert '#include "bn_regular_bg_items_m4_event_anim.h"' in event
    assert '#include "bn_sprite_items_m4_event_cecil.h"' in event
    assert "_model.begin(flow)" in event
    assert "_model.complete(flow)" in event


def test_m4_generated_progression_assets_are_declared_for_butano():
    for stem in (
        "m4_shop", "m4_catalog_anim", "m4_options_anim", "m4_event_anim", "m4_font",
        "m4_shop_keeper", "m4_shop_cursor", "m4_catalog_cursor", "m4_shop_sold_out",
        "m4_shop_buy_enabled", "m4_shop_locked", "m4_event_cecil",
    ):
        assert Path(f"graphics/{stem}.bmp").is_file()
        assert Path(f"graphics/{stem}.json").is_file()
    for character in range(6):
        stem = f"fishing_char_m4_{character}"
        assert Path(f"graphics/{stem}.bmp").is_file()
        assert Path(f"graphics/{stem}.json").is_file()


def test_m7_native_gba_has_no_image_mode_runtime_surface():
    native = "\n".join(
        p.read_text(encoding="utf-8")
        for p in list(Path("include").glob("*.h")) + list(Path("src").glob("*.cpp"))
    )
    for forbidden in ("image_option", "cycle_image_option", "cycle_image(", "_model.image(flow)"):
        assert forbidden not in native
    assert 'int image = 1' not in native


def test_m7_intro_is_real_cold_boot_scene_and_options_use_native_background():
    flow_h = Path("include/flow_model.h").read_text(encoding="utf-8")
    flow_cpp = Path("src/flow_model.cpp").read_text(encoding="utf-8")
    game_state_cpp = Path("src/game_state.cpp").read_text(encoding="utf-8")
    app_h = Path("include/app.h").read_text(encoding="utf-8")
    app_cpp = Path("src/app.cpp").read_text(encoding="utf-8")
    options_cpp = Path("src/options_scene.cpp").read_text(encoding="utf-8")

    assert "void complete_intro() noexcept" in flow_h
    assert "_state = GameState::Intro" in flow_h
    assert "GameState::Intro" in game_state_cpp
    assert 'return GameState::Intro' in game_state_cpp
    assert '#include "intro_scene.h"' in app_h
    assert "bn::optional<IntroScene>" in app_h
    assert "case GameState::Intro:" in app_cpp
    assert "_intro_scene.emplace()" in app_cpp
    assert "_intro_scene->update(_flow)" in app_cpp
    assert "complete_intro" in flow_cpp
    assert '#include "bn_regular_bg_items_m7_options_anim.h"' in options_cpp
    assert "bn_regular_bg_items_m4_options_anim" not in options_cpp


def test_m7_event_scene_uses_shared_recovered_dialog_system():
    header = Path("include/event_scene.h").read_text(encoding="utf-8")
    source = Path("src/event_scene.cpp").read_text(encoding="utf-8")
    assert '#include "dialog_model.h"' in header
    assert '#include "dialog_renderer.h"' in header
    assert "DialogModel _dialog" in header
    assert "DialogRenderer _dialog_renderer" in header
    assert "_text_offset" not in header
    assert "_last_page" not in header
    assert "_render_page" not in header
    assert "EVENT_DIALOG_OPEN_TICK = 100" in source
    assert "_dialog.update(bn::keypad::a_pressed())" in source
    assert "_dialog_renderer.render(_dialog)" in source



def test_m7_fishing_dialogs_and_global_presentation_effects_are_wired():
    fishing_header = Path("include/fishing_scene.h").read_text()
    fishing_source = Path("src/fishing_scene.cpp").read_text()
    app_header = Path("include/app.h").read_text()
    app_source = Path("src/app.cpp").read_text()
    assert "DialogModel _dialog" in fishing_header
    assert "DialogRenderer _dialog_renderer" in fishing_header
    assert "take_flash_request" in fishing_header
    assert "was caught!#You got " in fishing_source
    assert "The line broke..." in fishing_source
    assert "PresentationEffects _presentation" in app_header
    assert "bn::bg_palettes::set_fade_intensity" in app_source
    assert "bn::sprite_palettes::set_fade_intensity" in app_source



def test_multigraphic_sprites_leave_tile_data_uncompressed():
    """Butano cannot index compressed sprite tiles when a sheet contains multiple graphics."""
    offenders = []
    for metadata_path in sorted(Path("graphics").glob("*.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("type") != "sprite":
            continue

        bitmap_path = metadata_path.with_suffix(".bmp")
        if not bitmap_path.is_file():
            continue

        bitmap = bitmap_path.read_bytes()
        width, height = struct.unpack_from("<ii", bitmap, 18)
        frame_width = int(metadata.get("width", abs(width)))
        frame_height = int(metadata.get("height", abs(height)))
        graphics_count = (abs(width) // frame_width) * (abs(height) // frame_height)
        if graphics_count <= 1:
            continue

        tiles_compression = metadata.get("tiles_compression", metadata.get("compression", "none"))
        if tiles_compression != "none":
            offenders.append(f"{metadata_path.name}:{graphics_count}")

    assert not offenders, f"compressed multi-graphic sprite tiles are unsupported by Butano: {offenders}"

def test_multimap_regular_backgrounds_leave_map_data_uncompressed():
    """Butano cannot index compressed regular BG items that contain multiple maps."""
    offenders = []
    for metadata_path in sorted(Path("graphics").glob("*.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("type") != "regular_bg":
            continue

        bitmap_path = metadata_path.with_suffix(".bmp")
        if not bitmap_path.is_file():
            continue

        bitmap = bitmap_path.read_bytes()
        width, height = struct.unpack_from("<ii", bitmap, 18)
        frame_height = int(metadata.get("height", abs(height)))
        maps_count = abs(height) // frame_height
        if maps_count <= 1:
            continue

        if metadata.get("compression", "none") != "none" or metadata.get("map_compression", "none") != "none":
            offenders.append(f"{metadata_path.name}:{maps_count}")

    assert not offenders, f"compressed multi-map regular backgrounds are unsupported by Butano: {offenders}"


def test_shop_scene_matches_original_apk_text_boxes():
    source = Path("src/shop_scene.cpp").read_text(encoding="utf-8")

    # GameShop.init creates DrawText(92, 8, 126, 8) for the selected item name,
    # DrawText(32, 8, 24, 144) for price and DrawText(22, 8, 193, 144)
    # for the player's coin amount.
    assert "append_text(_text_sprites, item->name, 126, 8, 11)" in source
    assert "append_number(_text_sprites, item->price, 24, 144)" in source
    assert "append_money(_text_sprites, flow.money(), 193, 144)" in source

    # The Android original has no second-row status text in the Shop HUD.
    assert 'append_text(_text_sprites, "SOLD OUT"' not in source
    assert 'append_text(_text_sprites, "NO MONEY"' not in source
    assert 'append_text(_text_sprites, "BOUGHT"' not in source


def test_map_scene_restores_original_character_panel_and_gba_selection_feedback():
    header = Path("include/map_scene.h").read_text(encoding="utf-8")
    source = Path("src/map_scene.cpp").read_text(encoding="utf-8")

    # GameMap.draw renders tiles 171..176 at APK top-left (183, 91), while
    # GameMap.init creates the character-name DrawText at (168, 144), 48x8.
    for character in range(6):
        assert f'#include "bn_sprite_items_map_character_{character}.h"' in source
    assert "bn::sprite_items::map_character_0.create_sprite(79, 43, 0)" in source
    for character in range(1, 6):
        assert f"_character.set_item(bn::sprite_items::map_character_{character})" in source
    assert "m4_text_width(character_name, 6)" in source
    assert "field_x + (field_width - text_width) / 2" in source
    for name in ('"Cid"', '"Fran"', '"Leon"', '"Sazh"', '"Rosa"', '"Shadow"'):
        assert name in source

    # The original Catalog badge (tile 170) is restored when Catalog is owned.
    assert '#include "bn_sprite_items_map_catalog_parts.h"' in source
    assert "_catalog_parts" in header
    assert "map_target_enabled(MapTarget::Catalog)" in source

    # GBA-only D-pad feedback: selected target gets the recovered tile-165
    # corner cursor. Location-name text is intentionally not added.
    assert '#include "bn_sprite_items_m4_shop_cursor.h"' in source
    assert "_selection_cursor" in header
    for target, xy in (
        ("CrystalLake", "36, -48"),
        ("Pier", "20, 8"),
        ("Shop", "-12, -56"),
        ("River", "100, -56"),
        ("Ocean", "-4, 56"),
        ("Cave", "-92, 24"),
        ("Catalog", "-104, 72"),
    ):
        assert f"case MapTarget::{target}:" in source
        assert f"_selection_cursor.set_position({xy})" in source

    # Marker animation remains, but selected markers no longer blink now that
    # an explicit cursor frame exists.
    assert "_selection_ticks" not in header
    assert "selected_visible" not in source


def test_map_obj_assets_use_compatible_bpp4_palettes():
    metadata = json.loads(Path("graphics/map_spots.json").read_text(encoding="utf-8"))
    assert metadata["bpp_mode"] == "bpp_4"



def _bmp_rgb_at(path: Path, x: int, y: int) -> tuple[int, int, int]:
    data = path.read_bytes()
    assert data[:2] == b"BM"
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    height = struct.unpack_from("<i", data, 22)[0]
    assert dib_size == 40 and width > 0 and height > 0
    bpp = struct.unpack_from("<H", data, 28)[0]
    assert bpp == 8
    palette_offset = 14 + dib_size
    row_stride = (width + 3) & ~3
    row_from_bottom = height - 1 - y
    palette_index = data[pixel_offset + row_from_bottom * row_stride + x]
    blue, green, red, _ = struct.unpack_from("<BBBB", data, palette_offset + palette_index * 4)
    return red, green, blue


def test_shop_entry_requires_welcome_dialog_before_item_selection():
    header = Path("include/shop_scene.h").read_text(encoding="utf-8")
    source = Path("src/shop_scene.cpp").read_text(encoding="utf-8")

    # The touch APK starts the Shop with no item selected; the GBA adaptation
    # preserves that entrance beat with a modal welcome dialog before D-pad
    # selection becomes visible or actionable.
    assert "bool _welcome_active = true;" in header
    assert 'constexpr const char* SHOP_WELCOME_TEXT = "Welcome to Mari-Mari Shop";' in source
    assert "_dialog.start(SHOP_WELCOME_TEXT);" in source
    assert "_cursor.set_visible(false);" in source

    # While the welcome is active, only A is fed to DialogModel. In particular
    # B must not use the normal description-dialog cancel path, and no shop
    # movement/purchase input can run until the welcome fully closes.
    welcome_pos = source.index("if(_welcome_active)")
    normal_dialog_pos = source.index("else if(_dialog.active())", welcome_pos)
    welcome_block = source[welcome_pos:normal_dialog_pos]
    assert "_dialog.update(bn::keypad::a_pressed())" in welcome_block
    assert "bn::keypad::b_pressed()" not in welcome_block
    assert "_model.move_left()" not in welcome_block
    assert "_model.purchase(flow)" not in welcome_block
    assert "_welcome_active = false;" in welcome_block

    # Slot 0 becomes the visible D-pad selection only after the welcome closes.
    assert "_cursor.set_visible(! _welcome_active);" in source


def test_shop_scene_uses_spatial_four_way_dpad_navigation():
    header = Path("include/shop_model.h").read_text(encoding="utf-8")
    model = Path("src/shop_model.cpp").read_text(encoding="utf-8")
    scene = Path("src/shop_scene.cpp").read_text(encoding="utf-8")

    for method in ("move_left", "move_right", "move_up", "move_down"):
        assert f"void {method}() noexcept" in header
        assert f"ShopModel::{method}() noexcept" in model
        assert f"_model.{method}();" in scene

    assert "left_pressed() || bn::keypad::up_pressed()" not in scene
    assert "right_pressed() || bn::keypad::down_pressed()" not in scene


def test_shop_and_fishing_backgrounds_bake_original_drawtext_field_fill():
    # Android DrawText owns opaque 25,5,36 RGB backing bitmaps. The GBA port
    # bakes those static rectangles into the BG so dynamic glyph sprites do not
    # expose the decorative art underneath them.
    fill = (25, 5, 36)

    # All source 240x160 screens are centered at (+8,+48) in a 256x256 BG.
    for x, y in ((126, 8), (24, 144), (193, 144)):
        assert _bmp_rgb_at(Path("graphics/m4_shop.bmp"), x + 8, y + 48) == fill

    for stem in (
        "fishing_area_crystal", "fishing_area_pier", "fishing_area_river",
        "fishing_area_ocean", "fishing_area_cave",
    ):
        path = Path("graphics") / f"{stem}.bmp"
        for frame in range(3):
            frame_y = frame * 256
            assert _bmp_rgb_at(path, 126 + 8, frame_y + 8 + 48) == fill
            assert _bmp_rgb_at(path, 193 + 8, frame_y + 144 + 48) == fill


def test_fishing_scene_restores_original_hud_text_and_positions():
    header = Path("include/fishing_scene.h").read_text(encoding="utf-8")
    source = Path("src/fishing_scene.cpp").read_text(encoding="utf-8")

    assert '#include "bn_sprite_items_m4_font.h"' in source
    assert "_hud_text_sprites" in header
    for name in ('"Worm"', '"Bread"', '"Candy"', '"Bitter Gum"', '"Steak"', '"Rainboworm"', '"Bait X"'):
        assert name in source
    assert "append_text(_hud_text_sprites, bait_name, 126, 8, 11)" in source
    assert "append_money(_hud_text_sprites, flow.money(), 193, 144)" in source

    # APK top-left (220,4) for tile 98 => Butano center (108,-68).
    assert "fishing_hud.create_sprite(108, -68, 1)" in source
    # APK meter tile top-left Y=145 => Butano 8x8 center Y=69.
    assert "_meter.set_position(_model.meter_x() - 116, 69)" in source


def test_map_scene_does_not_add_gba_only_location_names():
    source = Path("src/map_scene.cpp").read_text(encoding="utf-8")
    # Keep the original APK character-name field, but no extra target-name UI.
    assert "m4_text_width(character_name, 6)" in source
    assert "field_x + (field_width - text_width) / 2" in source
    assert "TargetLabel" not in source
    assert "target_label(" not in source
    assert "append_centered_text" not in source
    for label in ('"Crystal Lake"', '"Pier"', '"Shop"', '"River"', '"Ocean"', '"Cave"', '"Catalog"'):
        assert label not in source


def test_runtime_parity_regressions_title_dialog_and_shop_cursor():
    fishing = Path("src/fishing_scene.cpp").read_text(encoding="utf-8")
    title = Path("src/title_scene.cpp").read_text(encoding="utf-8")
    shop = Path("src/shop_scene.cpp").read_text(encoding="utf-8")

    # A fresh catch/line-break dialogue must be allowed to restart the shared
    # DialogModel even after a previous dialogue reached its done() latch.
    assert "if(_model.dialog_alive() && ! _dialog.active())" in fishing
    assert "if(_model.dialog_alive() && ! _dialog.active() && ! _dialog.done())" not in fishing

    # The unsafe stacked multi-map title item stays out of runtime. The three
    # recovered sea frames are independent single-map BG items instead.
    assert '#include "bn_regular_bg_items_title_frame_112.h"' in title
    assert '#include "bn_regular_bg_items_title_frame_113.h"' in title
    assert '#include "bn_regular_bg_items_title_frame_114.h"' in title
    assert "flow.title_sea_tile()" in title
    assert "_background.set_item(bn::regular_bg_items::title_frame_113)" in title
    assert "_background.set_item(bn::regular_bg_items::title_frame_114)" in title
    assert "_background.set_item(bn::regular_bg_items::title_frame_112)" in title
    assert '#include "bn_regular_bg_items_title_anim.h"' not in title

    # Tile 165 is a 24x24 cursor padded at the top-left of a 32x32 OBJ. Shift
    # its sprite center by +4,+4 so the visible 24x24 box is centered on each
    # 24px-spaced Shop item.
    assert "m4_shop_cursor.create_sprite(16, -40, 0)" in shop
    assert "_cursor.set_position(16 + (slot % 4) * 24, -40 + (slot / 4) * 24)" in shop


def test_direct_sound_audio_is_not_reprocessed_by_dmg_pipeline():
    text = Path("Makefile").read_text(encoding="utf-8")
    assert "AUDIO := audio" in text
    assert "DMGAUDIO := audio" not in text
    assert "DMGAUDIO :=\n" in text


def test_parity_pass_restores_dialog_driven_shop_catalog_and_title_only_start():
    shop_h = Path("include/shop_scene.h").read_text(encoding="utf-8")
    shop = Path("src/shop_scene.cpp").read_text(encoding="utf-8")
    catalog_h = Path("include/catalog_scene.h").read_text(encoding="utf-8")
    catalog = Path("src/catalog_scene.cpp").read_text(encoding="utf-8")
    event = Path("src/event_scene.cpp").read_text(encoding="utf-8")
    intro = Path("src/intro_scene.cpp").read_text(encoding="utf-8")
    fishing = Path("src/fishing_scene.cpp").read_text(encoding="utf-8")

    assert "DialogModel _dialog" in shop_h
    assert "DialogRenderer _dialog_renderer" in shop_h
    assert "bn_sprite_items_m4_shop_locked.h" in shop
    assert "bn_sprite_items_m4_shop_buy_enabled.h" in shop
    assert "shop_item_locked" in shop
    assert "shop_item_purchasable" in shop
    assert "_keeper(bn::sprite_items::m4_shop_keeper.create_sprite(-64, 16, 0))" in shop
    assert "_dialog.talking()" in shop

    assert "DialogModel _dialog" in catalog_h
    assert "DialogRenderer _dialog_renderer" in catalog_h
    assert "_model.move_left()" in catalog
    assert "_model.move_right()" in catalog
    assert "_model.move_up()" in catalog
    assert "_model.move_down()" in catalog
    assert "bn::keypad::a_pressed()" in catalog
    assert "entry->description" in catalog

    assert "_cecil(bn::sprite_items::m4_event_cecil.create_sprite(-84, 24, 0))" in event
    assert "_dialog.talking()" in event
    assert "bn::keypad::select_pressed()" in intro
    assert "input.cancel_cast" in fishing

    # Current GBA mapping: START plays on Title and opens Catalog on Map only.
    title_source = Path("src/title_scene.cpp").read_text(encoding="utf-8")
    map_source = Path("src/map_scene.cpp").read_text(encoding="utf-8")
    assert "bn::keypad::start_pressed()" in title_source
    assert "bn::keypad::select_pressed()" in title_source
    assert "bn::keypad::start_pressed()" in map_source
    assert "open_catalog_from_map" in map_source
    for stem in ("intro", "fishing", "shop", "catalog", "event", "options"):
        assert "bn::keypad::start_pressed()" not in Path(f"src/{stem}_scene.cpp").read_text(encoding="utf-8")


def test_parity_pass_shop_assets_exist():
    for stem in ("m4_shop_locked", "m4_shop_buy_enabled"):
        assert Path(f"graphics/{stem}.bmp").is_file()
        assert Path(f"graphics/{stem}.json").is_file()


def test_shop_modal_descriptions_locked_cursor_and_konami_contract():
    shop_h = Path("include/shop_scene.h").read_text(encoding="utf-8")
    shop = Path("src/shop_scene.cpp").read_text(encoding="utf-8")
    model_h = Path("include/shop_model.h").read_text(encoding="utf-8")

    # Moving only selects; SELECT explicitly opens the description.
    assert "bn::keypad::select_pressed()" in shop
    assert "_start_description(flow);" in shop
    movement_block = shop[shop.index("if(moved)"):shop.index("else if(bn::keypad::select_pressed())")]
    assert "_start_description(flow);" not in movement_block

    # The modal dialog owns the bottom HUD while open, so money/price glyphs
    # cannot render over long descriptions or their advance marker.
    assert "if(_dialog.active())" in shop
    assert "_text_sprites.clear();" in shop
    assert "_dirty = true;" in shop

    # Locked Nova is opaque, so force it behind the cursor.
    assert "_locked_overlay.set_z_order(1)" in shop
    assert "_cursor.set_z_order(0)" in shop

    # Konami is Shop-only and tracks the canonical sequence.
    assert "enum class ShopCheatKey" in model_h
    assert "enum class ShopCheatResult" in model_h
    for key in ("Up", "Down", "Left", "Right", "B", "A"):
        assert f"ShopCheatKey::{key}" in shop
    assert "flow.grant_money(30)" in shop
    assert "AudioCue::Coin" in shop
    assert "300" in Path("src/shop_model.cpp").read_text(encoding="utf-8")


def test_dialog_glyph_bearings_and_shop_buy_indicator_position():
    dialog_renderer = Path("src/dialog_renderer.cpp").read_text(encoding="utf-8")
    shop = Path("src/shop_scene.cpp").read_text(encoding="utf-8")

    # The proportional font has glyphs touching the left edge of their 8x8
    # tile. The renderer must compensate those bearings so adjacent opaque
    # pixels still have one clear column between them.
    assert "dialog_character_draw_x_adjust(character)" in dialog_renderer

    # Canonical APK GameShop.draw(): tile 99 is drawn at screen (4, 140).
    # A 16x16 Butano OBJ at that top-left has center screen (12, 148), i.e.
    # world coordinates (-108, 68). The old y=72 placed it 4 px too low.
    assert "m4_shop_buy_enabled.create_sprite(-108, 68, 0)" in shop



def test_map_uses_spatial_dpad_directional_character_cycle_and_start_catalog():
    source = Path("src/map_scene.cpp").read_text(encoding="utf-8")
    assert "bn::keypad::left_pressed()" in source
    assert "bn::keypad::right_pressed()" in source
    assert "bn::keypad::up_pressed()" in source
    assert "bn::keypad::down_pressed()" in source
    assert "MapCommand::Left" in source
    assert "MapCommand::Right" in source
    assert "MapCommand::Up" in source
    assert "MapCommand::Down" in source
    assert "cycle_owned_character(-1)" in source
    assert "cycle_owned_character(1)" in source
    assert "bn::keypad::start_pressed()" in source
    assert "open_catalog_from_map" in source


def test_title_start_plays_select_opens_options_and_a_still_accepts_play():
    source = Path("src/title_scene.cpp").read_text(encoding="utf-8")
    assert "bn::keypad::a_pressed()" in source
    assert "bn::keypad::start_pressed()" in source
    assert "bn::keypad::select_pressed()" in source
    assert "bn::keypad::a_pressed() || bn::keypad::start_pressed()" in source
    assert "flow.handle_title_command(TitleCommand::Play);" in source
    select_pos = source.index("bn::keypad::select_pressed()")
    options_pos = source.index("TitleCommand::Options")
    assert options_pos > select_pos


def test_all_scene_m4_text_rendering_uses_shared_proportional_metrics():
    layout = Path("include/m4_text_layout.h")
    assert layout.is_file()
    layout_text = layout.read_text(encoding="utf-8")
    assert "m4_character_advance" in layout_text
    assert "m4_character_draw_x_adjust" in layout_text
    assert "m4_text_width" in layout_text

    for stem in ("map_scene.cpp", "shop_scene.cpp", "catalog_scene.cpp", "fishing_scene.cpp", "options_scene.cpp"):
        text = Path("src", stem).read_text(encoding="utf-8")
        assert '#include "m4_text_layout.h"' in text
        assert "column * 8" not in text
        assert "m4_character_advance" in text
        assert "m4_character_draw_x_adjust" in text

    map_text = Path("src/map_scene.cpp").read_text(encoding="utf-8")
    assert "m4_text_width" in map_text
    assert "CHARACTER_NAMES" in map_text
