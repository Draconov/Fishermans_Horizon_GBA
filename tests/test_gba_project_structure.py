from __future__ import annotations

from pathlib import Path


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


def test_title_scene_uses_generated_animated_reference_background_and_gba_input():
    text = Path("src/title_scene.cpp").read_text(encoding="utf-8")
    assert '#include "bn_regular_bg_items_title_anim.h"' in text
    assert '#include "bn_keypad.h"' in text
    assert "bn::regular_bg_items::title_anim.create_bg(0, 0, 0)" in text
    assert "bn::keypad::a_pressed()" in text
    assert "bn::keypad::start_pressed()" in text
    assert "set_map" in text


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
    for stem in ("title_anim", "map", "map_spots", "crystal_lake"):
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
    assert "cycle_owned_character()" in map_source

    event = Path("src/event_scene.cpp").read_text(encoding="utf-8")
    assert '#include "event_model.h"' in event
    assert '#include "bn_regular_bg_items_m4_event_anim.h"' in event
    assert '#include "bn_sprite_items_m4_event_cecil.h"' in event
    assert "_model.begin(flow)" in event
    assert "_model.complete(flow)" in event


def test_m4_generated_progression_assets_are_declared_for_butano():
    for stem in (
        "m4_shop", "m4_catalog_anim", "m4_options_anim", "m4_event_anim", "m4_font",
        "m4_shop_keeper", "m4_shop_cursor", "m4_catalog_cursor", "m4_shop_sold_out", "m4_event_cecil",
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
