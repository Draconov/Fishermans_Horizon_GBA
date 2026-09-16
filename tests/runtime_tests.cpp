// Consolidated standalone runtime contracts.

// ---- test_audio_policy.cpp ----
#include <cassert>

#include "audio_policy.h"

void test_audio_policy_contract()
{
    using fh::AudioCue;
    using fh::SceneTrack;

    assert(fh::scene_track(fh::GameState::Title) == SceneTrack::Title);
    assert(fh::scene_track(fh::GameState::Map) == SceneTrack::MariMari);
    assert(fh::scene_track(fh::GameState::Shop) == SceneTrack::Select);
    assert(fh::scene_track(fh::GameState::Catalog) == SceneTrack::Select);
    assert(fh::scene_track(fh::GameState::Event) == SceneTrack::Welcome);
    assert(fh::scene_track(fh::GameState::Fishing) == SceneTrack::Inherit);
    assert(fh::scene_track(fh::GameState::Options) == SceneTrack::Title);
    assert(fh::scene_track(fh::GameState::Intro) == SceneTrack::None);

    assert(fh::scene_track_loop_frames(SceneTrack::Title) == 2472);
    assert(fh::scene_track_loop_frames(SceneTrack::MariMari) == 209);
    assert(fh::scene_track_loop_frames(SceneTrack::Select) == 209);
    assert(fh::scene_track_loop_frames(SceneTrack::Welcome) == 414);
    assert(fh::scene_track_loop_frames(SceneTrack::None) == 0);
    assert(fh::scene_track_loop_frames(SceneTrack::Inherit) == 0);

    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::None) == AudioCue::None);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::NextPage) == AudioCue::NextPage);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Throw) == AudioCue::Throw);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::LineBreak) == AudioCue::LineBreak);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Coin) == AudioCue::Coin);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::FishCatchBait) == AudioCue::FishCatchBait);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Water) == AudioCue::Water);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Fanfare) == AudioCue::Fanfare);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Coil) == AudioCue::Coil);
}


// ---- test_catalog_model.cpp ----
#include <array>
#include <cassert>
#include <cstring>

#include "catalog_content.h"
#include "catalog_model.h"
#include "flow_model.h"

void test_catalog_model_contract()
{
    assert(fh::catalog_entry_count() == 44);

    // Catalog fish/cursor anchors must match the 11 hooks on each background rack.
    assert(fh::catalog_slot_screen_x(0) == 39);
    assert(fh::catalog_slot_screen_x(10) == 199);
    assert(fh::catalog_slot_screen_x(11) == 39);
    assert(fh::catalog_slot_screen_y(0) == 39);
    assert(fh::catalog_slot_screen_y(10) == 39);
    assert(fh::catalog_slot_screen_y(11) == 63);
    assert(fh::catalog_slot_screen_y(33) == 111);

    constexpr std::array<int, 5> FIRST_NUMBERS = {3, 4, 5, 1, 2};
    constexpr std::array<const char*, 5> FIRST_NAMES = {"BOOT", "CAN", "PLASTIC BAG", "SIRIRIDINE", "DRAGFISH"};
    std::array<bool, 45> seen = {};
    for(int cursor = 0; cursor < 44; ++cursor)
    {
        const fh::CatalogEntrySpec* entry = fh::catalog_entry_spec(cursor);
        assert(entry);
        assert(entry->cursor == cursor);
        assert(entry->fish_number >= 1 && entry->fish_number <= 44);
        assert(! seen[entry->fish_number]);
        seen[entry->fish_number] = true;
        assert(entry->name && entry->name[0] != '\0');
        assert(entry->description && entry->description[0] != '\0');
        if(cursor < 5)
        {
            assert(entry->fish_number == FIRST_NUMBERS[cursor]);
            assert(std::strcmp(entry->name, FIRST_NAMES[cursor]) == 0);
        }
    }
    assert(fh::catalog_entry_spec(-1) == nullptr);
    assert(fh::catalog_entry_spec(44) == nullptr);
    const fh::CatalogEntrySpec* last = fh::catalog_entry_spec(43);
    assert(last && last->fish_number == 44);
    assert(std::strcmp(last->name, "???") == 0);

    fh::ProgressState progress;
    fh::FlowModel flow(progress);
    fh::CatalogModel catalog;
    assert(catalog.selected_cursor() == 0);
    assert(catalog.selected_entry()->fish_number == 3);
    assert(! catalog.selected_caught(flow));

    flow.apply_fishing_reward(3, 0);
    assert(catalog.selected_caught(flow));
    catalog.next();
    assert(catalog.selected_cursor() == 1);
    assert(catalog.selected_entry()->fish_number == 4);
    catalog.previous();
    assert(catalog.selected_cursor() == 0);
    catalog.previous();
    assert(catalog.selected_cursor() == 43);
    catalog.next();
    assert(catalog.selected_cursor() == 0);
    catalog.select(43);
    assert(catalog.selected_cursor() == 43);
    catalog.select(-1);
    assert(catalog.selected_cursor() == 43);
    catalog.select(44);
    assert(catalog.selected_cursor() == 43);

    assert(! catalog.complete(flow));
    for(int fish = 1; fish <= 44; ++fish)
    {
        flow.apply_fishing_reward(fish, 0);
    }
    assert(catalog.complete(flow));

    {
        fh::CatalogModel spatial;
        spatial.move_left();
        spatial.move_up();
        assert(spatial.selected_cursor() == 0);
        spatial.move_right();
        assert(spatial.selected_cursor() == 1);
        spatial.move_down();
        assert(spatial.selected_cursor() == 12);
        spatial.move_down();
        assert(spatial.selected_cursor() == 23);
        spatial.move_down();
        assert(spatial.selected_cursor() == 34);
        spatial.move_down();
        assert(spatial.selected_cursor() == 34);
        spatial.move_left();
        assert(spatial.selected_cursor() == 33);
        spatial.move_up();
        assert(spatial.selected_cursor() == 22);
        spatial.select(43);
        spatial.move_right();
        spatial.move_down();
        assert(spatial.selected_cursor() == 43);
    }
}


// ---- test_dialog_model.cpp ----
#include <cassert>
#include <cstring>

#include "dialog_model.h"
#include "dialog_layout.h"
#include "progression_content.h"

void test_dialog_model_contract()
{
    {
        fh::DialogModel dialog("first#second##third");
        assert(dialog.box_y() == 160);
        assert(dialog.page_index() == 0);
        assert(! dialog.waiting_for_advance());
        assert(! dialog.done());

        // Original box slides from y=160 to y=136 by 2 pixels/update.
        for(int i = 0; i < 12; ++i)
        {
            assert(dialog.update(false) == fh::DialogEvent::None);
        }
        assert(dialog.box_y() == 136);
        assert(dialog.talking());

        // One source character is consumed per visible update. Two visible
        // lines fill the first page at the second '#'.
        while(! dialog.waiting_for_advance())
        {
            assert(dialog.update(false) == fh::DialogEvent::None);
        }
        assert(dialog.page_index() == 0);
        assert(dialog.visible_end() > dialog.page_start());
        assert(! dialog.talking());

        assert(dialog.update(true) == fh::DialogEvent::NextPage);
        assert(dialog.page_index() == 1);
        assert(! dialog.waiting_for_advance());

        while(! dialog.waiting_for_advance())
        {
            dialog.update(false);
        }
        assert(dialog.update(true) == fh::DialogEvent::NextPage);
        assert(! dialog.done());

        // Closing slides the box back down before becoming done.
        for(int i = 0; i < 11; ++i)
        {
            assert(dialog.update(false) == fh::DialogEvent::None);
            assert(! dialog.done());
        }
        assert(dialog.update(false) == fh::DialogEvent::Closed);
        assert(dialog.done());
        assert(dialog.box_y() == 160);
    }

    {
        // '#' advances one line and '@' advances a paragraph (two lines).
        fh::DialogModel dialog("A#B@C");
        for(int i = 0; i < 12; ++i) dialog.update(false);
        dialog.update(false); // A
        assert(dialog.cursor_x() == 15);
        assert(dialog.cursor_y() == 4);
        dialog.update(false); // #
        assert(dialog.cursor_x() == 8);
        assert(dialog.cursor_y() == 13);
        dialog.update(false); // B
        assert(dialog.cursor_x() == 15);
        dialog.update(false); // @
        assert(dialog.cursor_x() == 8);
        assert(dialog.cursor_y() == 31);
        assert(dialog.waiting_for_advance());
    }

    {
        // Leading spaces do not shift the original x=8 origin.
        fh::DialogModel dialog(" A");
        for(int i = 0; i < 12; ++i) dialog.update(false);
        dialog.update(false);
        assert(dialog.cursor_x() == 8);
        dialog.update(false);
        assert(dialog.cursor_x() == 15);
    }

    {
        fh::DialogModel dialog("temporary");
        assert(dialog.active());
        dialog.clear();
        assert(! dialog.active());
        assert(! dialog.talking());
        assert(! dialog.done());
    }

    {
        // Every Shop description must paginate through the shared DialogBox
        // without overflowing/stalling, including the longest character blurbs.
        for(int slot = 0; slot < fh::shop_item_count(); ++slot)
        {
            const fh::ShopItemSpec* item = fh::shop_item_spec(slot);
            assert(item);
            fh::DialogModel dialog(item->description);
            int guard = 0;
            while(! dialog.done() && guard < 1000)
            {
                const bool advance = dialog.waiting_for_advance();
                dialog.update(advance);
                assert(dialog.cursor_x() <= 210);
                ++guard;
            }
            assert(dialog.done());
            assert(guard < 1000);
        }
    }


    {
        // Dialog glyph placement keeps exactly one blank pixel between opaque
        // glyph bounds, including wide/edge-touching glyphs from ui_font.bmp.
        assert(fh::dialog_character_advance('A') == 7);
        assert(fh::dialog_character_advance('i') == 3);
        assert(fh::dialog_character_advance('m') == 9);
        assert(fh::dialog_character_advance('p') == 8);
        assert(fh::dialog_character_advance('q') == 8);
        assert(fh::dialog_character_advance('Q') == 8);
        assert(fh::dialog_character_advance(':') == 3);

        assert(fh::dialog_character_draw_x_adjust('A') == 0);
        assert(fh::dialog_character_draw_x_adjust('m') == 1);
        assert(fh::dialog_character_draw_x_adjust('w') == 1);
        assert(fh::dialog_character_draw_x_adjust('M') == 1);
        assert(fh::dialog_character_draw_x_adjust('W') == 1);
        assert(fh::dialog_character_draw_x_adjust('p') == 1);
        assert(fh::dialog_character_draw_x_adjust('q') == 0);
    }
}


// ---- test_event_model.cpp ----
#include <cassert>
#include <cstring>

#include "event_model.h"
#include "flow_model.h"

namespace
{

void enter_catalog(fh::FlowModel& flow)
{
    flow.handle_title_command(fh::TitleCommand::Play);
    assert(flow.state() == fh::GameState::Map);
    while(flow.selected_map_target() != fh::MapTarget::Catalog)
    {
        flow.handle_map_command(fh::MapCommand::NextTarget);
    }
    flow.handle_map_command(fh::MapCommand::Confirm);
    assert(flow.state() == fh::GameState::Catalog);
}

}

void test_event_model_contract()
{
    {
        fh::ProgressState progress;
        progress.prologue_complete = false;
        fh::FlowModel flow(progress);
        flow.complete_intro();
        flow.handle_title_command(fh::TitleCommand::Play);
        assert(flow.state() == fh::GameState::Event);
        assert(flow.event_id() == 1);

        fh::EventModel event(flow.event_id());
        assert(event.id() == 1);
        assert(std::strstr(event.text(), "Cecil") != nullptr);
        event.begin(flow);
        assert(flow.event_id() == 1);
        event.complete(flow);
        assert(flow.state() == fh::GameState::Map);
        assert(flow.prologue_complete());
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.catalog = true;
        fh::FlowModel flow(progress);
        flow.complete_intro();
        enter_catalog(flow);
        flow.handle_catalog_back(true);
        assert(flow.state() == fh::GameState::Event);
        assert(flow.event_id() == 2);

        fh::EventModel ending(flow.event_id());
        assert(ending.id() == 2);
        assert(std::strstr(ending.text(), "caught all") != nullptr);
        ending.begin(flow);
        assert(flow.event_id() == 3);
        ending.complete(flow);
        assert(flow.state() == fh::GameState::Map);
        assert(flow.prologue_complete());

        // Event 3 blocks the all-fish ending from retriggering in the same runtime.
        while(flow.selected_map_target() != fh::MapTarget::Catalog)
        {
            flow.handle_map_command(fh::MapCommand::NextTarget);
        }
        flow.handle_map_command(fh::MapCommand::Confirm);
        assert(flow.state() == fh::GameState::Catalog);
        flow.handle_catalog_back(true);
        assert(flow.state() == fh::GameState::Map);
        assert(flow.event_id() == 3);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.catalog = true;
        fh::FlowModel flow(progress);
        flow.complete_intro();
        enter_catalog(flow);
        flow.handle_catalog_back(false);
        assert(flow.state() == fh::GameState::Map);
        assert(flow.event_id() == 0);
    }
}


// ---- test_fishing_content.cpp ----
#include <cassert>
#include <cstdint>
#include <cstring>

#include "fishing_content.h"

namespace
{

void hash_byte(std::uint64_t& hash, unsigned char value)
{
    hash ^= value;
    hash *= 1099511628211ULL;
}

void hash_int(std::uint64_t& hash, int value)
{
    std::uint32_t encoded = static_cast<std::uint32_t>(value);
    for(int shift = 0; shift < 32; shift += 8)
    {
        hash_byte(hash, static_cast<unsigned char>((encoded >> shift) & 0xFF));
    }
}

void hash_string(std::uint64_t& hash, const char* text)
{
    while(*text)
    {
        hash_byte(hash, static_cast<unsigned char>(*text++));
    }
    hash_byte(hash, 0);
}

}

void test_fishing_content_contract()
{
    assert(fh::fishing_area_count() == 6);
    assert(fh::fishing_area_spec(0).pool == 1);
    assert(fh::fishing_area_spec(99).pool == 1);

    assert(std::strcmp(fh::fish_for_roll(1, 1)->name, "BOOT") == 0);
    assert(std::strcmp(fh::fish_for_roll(2, 9)->name, "TROLLSHARK") == 0);
    assert(std::strcmp(fh::fish_for_roll(3, 9)->name, "PINKSHARK") == 0);
    assert(std::strcmp(fh::fish_for_roll(4, 9)->name, "HAMMERHEAD") == 0);
    assert(std::strcmp(fh::fish_for_roll(5, 9)->name, "???") == 0);
    assert(std::strcmp(fh::fish_for_roll(6, 9)->name, "TROLLSHARK") == 0);
    assert(fh::fish_for_roll(1, 0) == nullptr);
    assert(fh::fish_for_roll(6, 10) == nullptr);

    std::uint64_t hash = 1469598103934665603ULL;
    for(int pool = 1; pool <= fh::fishing_area_count(); ++pool)
    {
        const fh::FishingAreaSpec& area = fh::fishing_area_spec(pool);
        hash_int(hash, area.pool);
        for(int roll = 1; roll <= 9; ++roll)
        {
            const fh::FishSpec* fish = fh::fish_for_roll(pool, roll);
            assert(fish);
            hash_string(hash, fish->name);
            hash_int(hash, fish->number);
            hash_int(hash, fish->difficulty);
            hash_int(hash, fish->bait);
            hash_int(hash, fish->movement);
            hash_int(hash, fish->distance);
            hash_int(hash, fish->sprite);
            hash_int(hash, fish->reward);
        }
    }
    assert(hash == 0x407DAD1EBA58EF02ULL);
}


// ---- test_fishing_model.cpp ----
#include <cassert>
#include <cmath>

#include "fishing_model.h"

namespace
{

void step(fh::FishingModel& model, bool held = false, int roll = 0, bool confirm = false, bool cancel = false)
{
    fh::FishingInput input;
    input.rod_held = held;
    input.confirm_dialog = confirm;
    input.cancel_cast = cancel;
    model.update(input, roll);
}

void advance_to_stand(fh::FishingModel& model)
{
    step(model);
    assert(model.state() == fh::FishingState::Stand);
}

void drain_sounds(fh::FishingModel& model)
{
    while(model.take_sound_event() != fh::FishingSoundEvent::None)
    {
    }
}

void cast_with_charge_frames(fh::FishingModel& model, int charge_frames)
{
    advance_to_stand(model);
    step(model, true); // STAND -> GET_READY, ticks reset to zero.
    assert(model.state() == fh::FishingState::GetReadyToThrow);

    for(int index = 0; index < charge_frames; ++index)
    {
        step(model, true);
    }

    while(model.state() == fh::FishingState::GetReadyToThrow)
    {
        step(model, false);
    }
    assert(model.state() == fh::FishingState::Throw);
}

void advance_to_bait(fh::FishingModel& model, int roll = 0)
{
    int guard = 200;
    while(model.state() == fh::FishingState::Throw && --guard)
    {
        step(model, false, roll);
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::BaitInWater);
}

void hook_boot(fh::FishingModel& model)
{
    cast_with_charge_frames(model, 37); // max meter, distance 248.
    advance_to_bait(model, 1);

    int guard = 220;
    while(model.state() == fh::FishingState::BaitInWater && --guard)
    {
        step(model, true, 1);
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishInLine);
    assert(model.current_fish_number() == 3);
}

void hook_unicuda(fh::FishingModel& model)
{
    cast_with_charge_frames(model, 37);
    advance_to_bait(model, 9);

    int guard = 300;
    int phase = 0;
    while(model.state() == fh::FishingState::BaitInWater && --guard)
    {
        // Keep bait movement at class 1 instead of letting held motion reach 10.
        const bool held = phase < 12;
        step(model, held, 9);
        phase = (phase + 1) % 28;
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishInLine);
    assert(model.current_fish_number() == 41);
}

void hook_movement_one(fh::FishingModel& model, int roll, int expected_fish_number)
{
    cast_with_charge_frames(model, 37);
    advance_to_bait(model, roll);

    int guard = 320;
    int phase = 0;
    while(model.state() == fh::FishingState::BaitInWater && --guard)
    {
        const bool held = phase < 12;
        step(model, held, roll);
        phase = (phase + 1) % 28;
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishInLine);
    assert(model.current_fish_number() == expected_fish_number);
}

void hook_movement_two(fh::FishingModel& model, int roll, int expected_fish_number)
{
    cast_with_charge_frames(model, 37);
    advance_to_bait(model, roll);

    int guard = 240;
    while(model.state() == fh::FishingState::BaitInWater && --guard)
    {
        step(model, true, roll);
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishInLine);
    assert(model.current_fish_number() == expected_fish_number);
}

void catch_boot(fh::FishingModel& model)
{
    hook_boot(model);
    int guard = 1000;
    int phase = 0;
    while(model.state() == fh::FishingState::FishInLine && --guard)
    {
        // Refill the tension meter periodically while still making net progress.
        const bool held = phase < 80;
        step(model, held, 0);
        phase = (phase + 1) % 120;
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishCatch);
}

}

void test_fishing_model_contract()
{
    static_assert(int(fh::FishingState::Init) == 0);
    static_assert(int(fh::FishingState::Stand) == 1);
    static_assert(int(fh::FishingState::Recoil) == 2);
    static_assert(int(fh::FishingState::GetReadyToThrow) == 3);
    static_assert(int(fh::FishingState::Throw) == 4);
    static_assert(int(fh::FishingState::BaitInWater) == 5);
    static_assert(int(fh::FishingState::FishInLine) == 6);
    static_assert(int(fh::FishingState::LineBreak) == 7);
    static_assert(int(fh::FishingState::FishCatch) == 8);
    static_assert(int(fh::FishingState::Reward) == 9);

    {
        fh::FishingModel crystal(1, 0, 0);
        fh::FishingModel pier(2, 1, 0);
        fh::FishingModel river(3, 2, 0);
        fh::FishingModel invalid(99, 0, 0);
        assert(crystal.pool() == 1);
        assert(pier.pool() == 2);
        assert(river.pool() == 3);
        assert(invalid.pool() == 1);
        assert(crystal.stick_strength() == 10);
        assert(pier.stick_strength() == 12);
        assert(river.stick_strength() == 14);
    }

    {
        fh::FishingModel pier(2, 0, 0);
        hook_movement_two(pier, 1, 4); // CAN
    }

    {
        fh::FishingModel river(3, 0, 0);
        hook_movement_one(river, 4, 30); // NOTTODAY
    }

    {
        fh::FishingModel ocean(4, 0, 0);
        hook_movement_two(ocean, 1, 5); // PLASTIC BAG
    }

    {
        fh::FishingModel cave(5, 0, 0);
        hook_movement_one(cave, 2, 21); // ILL-EEL
    }

    {
        fh::FishingModel model(1, 0, 0);
        assert(model.state() == fh::FishingState::Init);
        assert(model.sea_tile() == 112);
        assert(model.meter_x() == 37);
        assert(std::abs(model.line_distance() - 50.0f) < 0.001f);
        assert(model.stick_strength() == 10);
        assert(model.equipped_bait() == 0);
        model.set_equipped_bait(5);
        assert(model.equipped_bait() == 5);
        assert(model.bait_sprite() == 90);
        model.set_equipped_bait(99);
        assert(model.equipped_bait() == 5);
        model.set_equipped_bait(0);
        assert(model.equipped_bait() == 0);
        advance_to_stand(model);
        assert(model.ticks() == 0);
        assert(model.sea_tile() == 113);
        for(int frame = 2; frame <= 49; ++frame)
        {
            step(model);
            if(frame == 13) assert(model.sea_tile() == 114);
            if(frame == 25) assert(model.sea_tile() == 113);
            if(frame == 37) assert(model.sea_tile() == 112);
            if(frame == 49) assert(model.sea_tile() == 112);
        }
        step(model);
        assert(model.sea_tile() == 113);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 0);
        for(int index = 0; index < 10; ++index)
        {
            step(model);
        }
        assert(model.throw_delay() == 0);
        while(model.state() == fh::FishingState::Throw)
        {
            step(model);
        }
        assert(std::abs(model.line_distance() - 100.0f) < 0.001f);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 13); // 37 + 26 -> middle bucket.
        for(int index = 0; index < 10; ++index)
        {
            step(model);
        }
        assert(model.throw_delay() == 6);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 37); // max 111 -> high bucket.
        for(int index = 0; index < 10; ++index)
        {
            step(model);
        }
        assert(model.throw_delay() == 12);
        advance_to_bait(model);
        assert(std::abs(model.line_distance() - 248.0f) < 0.001f);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 37);
        advance_to_bait(model);
        assert(model.needs_random_roll());
        step(model, false, 7);
        assert(! model.needs_random_roll());
        assert(model.bait_move_points() == 0);
        assert(model.bait_movement_type() == 0);
        for(int index = 0; index < 13; ++index)
        {
            step(model, true, 0);
        }
        assert(model.bait_move_points() == 1);
        assert(model.bait_movement_type() == 1);
        for(int index = 0; index < 108; ++index)
        {
            step(model, true, 0);
        }
        assert(model.bait_move_points() == 10);
        assert(model.bait_movement_type() == 2);
        for(int index = 0; index < 24; ++index)
        {
            step(model, false, 0);
        }
        assert(model.bait_move_points() == 9);
        assert(model.bait_movement_type() == 1);
    }

    {
        // Roll zero is intentionally empty in Crystal Lake even when all lure
        // conditions match BOOT.
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 37);
        advance_to_bait(model, 0);
        for(int index = 0; index < 180; ++index)
        {
            step(model, true, 0);
        }
        assert(model.state() != fh::FishingState::FishInLine);
        assert(model.current_fish_number() == 0);
    }

    {
        // BOOT is wildcard bait but requires movement class 2 and 10
        // consecutive qualified lure checks.
        fh::FishingModel model(1, 0, 0);
        hook_boot(model);
        assert(model.current_fish_number() == 3);
        assert(model.current_fish_strength() == 4);
        step(model, true, 0);
        step(model, true, 0);
        assert(model.current_stamina() == 0);
        assert(model.current_fish_strength() == 1);
    }

    {
        // UNICUDA remains strong long enough for the original tension meter to
        // hit its lower bound while the player keeps holding the rod.
        fh::FishingModel model(1, 0, 5);
        hook_unicuda(model);
        int guard = 220;
        while(model.state() == fh::FishingState::FishInLine && --guard)
        {
            step(model, true, 0);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::LineBreak);
        assert(model.meter_x() <= 37);
    }

    {
        // Releasing against UNICUDA lets the line exceed 280 and breaks it.
        fh::FishingModel model(1, 0, 5);
        hook_unicuda(model);
        int guard = 160;
        while(model.state() == fh::FishingState::FishInLine && --guard)
        {
            step(model, false, 0);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::LineBreak);
        assert(model.line_distance() > 280.0f);

        while(model.state() == fh::FishingState::LineBreak && ! model.dialog_alive())
        {
            step(model);
        }
        assert(model.dialog_kind() == fh::FishingDialog::LineBreak);
        step(model, false, 0, true);
        assert(model.state() == fh::FishingState::Init);
    }

    {
        fh::FishingModel model(1, 0, 0);
        catch_boot(model);
        assert(model.line_distance() <= 48.0f);
        while(model.state() == fh::FishingState::FishCatch && ! model.dialog_alive())
        {
            step(model);
        }
        assert(model.dialog_kind() == fh::FishingDialog::Catch);
        assert(model.dialog_fish_name() != nullptr);
        step(model, false, 0, true);
        assert(model.state() == fh::FishingState::Reward);

        fh::FishingReward reward;
        int guard = 80;
        while(! reward.valid && --guard)
        {
            step(model);
            reward = model.take_reward();
        }
        assert(guard > 0);
        assert(reward.valid);
        assert(reward.fish_number == 3);
        assert(reward.amount == 1);
        assert(! model.take_reward().valid);
    }

    {
        // Reeling an empty cast all the way back enters recoil and eventually
        // returns through INIT.
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 10);
        advance_to_bait(model, 0);
        int guard = 600;
        while(model.state() == fh::FishingState::BaitInWater && --guard)
        {
            step(model, true, 0);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::Recoil);
        while(model.state() == fh::FishingState::Recoil && --guard)
        {
            step(model);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::Init);
    }


    {
        fh::FishingModel model(1, 0, 0);
        assert(model.take_sound_event() == fh::FishingSoundEvent::None);
        model.set_equipped_bait(5);
        assert(model.take_sound_event() == fh::FishingSoundEvent::NextPage);
        assert(model.take_sound_event() == fh::FishingSoundEvent::None);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 0);
        bool heard_throw = false;
        bool heard_water = false;
        int guard = 100;
        while(model.state() == fh::FishingState::Throw && --guard)
        {
            step(model);
            const fh::FishingSoundEvent event = model.take_sound_event();
            heard_throw |= event == fh::FishingSoundEvent::Throw;
            heard_water |= event == fh::FishingSoundEvent::Water;
        }
        assert(guard > 0);
        assert(heard_throw);
        assert(heard_water);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 37);
        advance_to_bait(model, 1);
        drain_sounds(model);
        bool heard_hook = false;
        int guard = 240;
        while(model.state() == fh::FishingState::BaitInWater && --guard)
        {
            step(model, true, 1);
            fh::FishingSoundEvent event = model.take_sound_event();
            heard_hook |= event == fh::FishingSoundEvent::FishCatchBait;
        }
        assert(guard > 0);
        assert(heard_hook);
    }

    {
        fh::FishingModel model(1, 0, 5);
        hook_unicuda(model);
        drain_sounds(model);
        while(model.state() == fh::FishingState::FishInLine)
        {
            step(model, true, 0);
            (void) model.take_sound_event();
        }
        assert(model.state() == fh::FishingState::LineBreak);
        step(model);
        assert(model.take_sound_event() == fh::FishingSoundEvent::LineBreak);
    }

    {
        fh::FishingModel model(1, 0, 0);
        catch_boot(model);
        drain_sounds(model);
        step(model);
        assert(model.take_sound_event() == fh::FishingSoundEvent::Water);

        bool heard_fanfare = false;
        while(model.state() == fh::FishingState::FishCatch && ! model.dialog_alive())
        {
            step(model);
            heard_fanfare |= model.take_sound_event() == fh::FishingSoundEvent::Fanfare;
        }
        assert(heard_fanfare);
        step(model, false, 0, true);
        assert(model.state() == fh::FishingState::Reward);

        bool heard_coin = false;
        int guard = 30;
        while(! heard_coin && --guard)
        {
            step(model);
            heard_coin |= model.take_sound_event() == fh::FishingSoundEvent::Coin;
        }
        assert(heard_coin);
    }

    {
        // SELECT cancels an unhooked cast through Recoil so A can cast again.
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 20);
        advance_to_bait(model, 0);
        assert(model.state() == fh::FishingState::BaitInWater);
        step(model, false, 0, false, true);
        assert(model.state() == fh::FishingState::Recoil);
        int guard = 120;
        while(model.state() != fh::FishingState::Stand && --guard)
        {
            step(model);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::Stand);
    }
}


// ---- test_flow_model.cpp ----
#include <cassert>

#include "flow_model.h"

namespace
{

void advance_title(fh::FlowModel& model, int updates)
{
    for(int index = 0; index < updates; ++index)
    {
        model.update_title_animation();
    }
}

void advance_map(fh::FlowModel& model, int updates)
{
    for(int index = 0; index < updates; ++index)
    {
        model.update_map_markers();
    }
}

}

void test_flow_model_contract()
{
    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(model.state() == fh::GameState::Title);
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.state() == fh::GameState::Map);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = false;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.state() == fh::GameState::Event);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Options);
        assert(model.state() == fh::GameState::Options);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(model.title_sea_tile() == 112);
        advance_title(model, 1);
        assert(model.title_sea_tile() == 113);
        advance_title(model, 12);
        assert(model.title_sea_tile() == 114);
        advance_title(model, 12);
        assert(model.title_sea_tile() == 113);
        advance_title(model, 12);
        assert(model.title_sea_tile() == 112);
        advance_title(model, 12);
        assert(model.title_sea_tile() == 112);
        assert(model.title_ticks() == 0);
        advance_title(model, 1);
        assert(model.title_sea_tile() == 113);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.handle_map_command(fh::MapCommand::Back);
        assert(model.state() == fh::GameState::Title);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Fishing);
        assert(model.fishing_pool() == 1);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.club_card = false;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(! model.map_target_enabled(fh::MapTarget::River));
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.map_spot_a_tile() == 100);
        assert(model.map_spot_b_tile() == 102);
        advance_map(model, 10);
        assert(model.map_spot_a_tile() == 100);
        assert(model.map_spot_b_tile() == 102);
        advance_map(model, 1);
        assert(model.map_spot_a_tile() == 101);
        assert(model.map_spot_b_tile() == 103);
        advance_map(model, 10);
        assert(model.map_spot_a_tile() == 100);
        assert(model.map_spot_b_tile() == 102);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
        model.handle_map_command(fh::MapCommand::NextTarget);
        assert(model.selected_map_target() == fh::MapTarget::Pier);
        model.handle_map_command(fh::MapCommand::NextTarget);
        assert(model.selected_map_target() == fh::MapTarget::Shop);
        // River/Ocean/Cave/Catalog are skipped while locked.
        model.handle_map_command(fh::MapCommand::NextTarget);
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Fishing);
        model.handle_fishing_back();
        assert(model.state() == fh::GameState::Map);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(model.money() == 10);
        assert(model.current_rod() == 0);
        assert(model.equipped_bait() == 0);
        assert(model.bait_owned(0));
        for(int bait = 1; bait < 7; ++bait)
        {
            assert(! model.bait_owned(bait));
        }
        for(int fish = 1; fish <= 44; ++fish)
        {
            assert(! model.catalog_has_fish(fish));
        }

        model.apply_fishing_reward(3, 1);
        assert(model.money() == 11);
        assert(model.catalog_has_fish(3));
        assert(! model.catalog_has_fish(2));

        model.apply_fishing_reward(41, 25);
        assert(model.money() == 36);
        assert(model.catalog_has_fish(41));

        model.apply_fishing_reward(40, 5000);
        assert(model.money() == 999);
        assert(model.catalog_has_fish(40));
        model.apply_fishing_reward(0, 10);
        model.apply_fishing_reward(45, 10);
        assert(model.money() == 999);
    }


    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.bait_owned = {true, false, true, false, false, true, false};
        progress.equipped_bait = 0;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(model.cycle_owned_bait(1) == 2);
        assert(model.equipped_bait() == 2);
        assert(model.cycle_owned_bait(-1) == 0);
        assert(model.cycle_owned_bait(-1) == 5);
        assert(model.cycle_owned_bait(1) == 0);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.handle_map_command(fh::MapCommand::NextTarget); // Pier
        assert(model.selected_map_target() == fh::MapTarget::Pier);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Fishing);
        assert(model.fishing_pool() == 2);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.club_card = true;
        progress.old_boat = true;
        progress.ancient_map = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        for(int expected_pool = 2; expected_pool <= 5; ++expected_pool)
        {
            model.handle_map_command(fh::MapCommand::NextTarget);
            if(expected_pool == 3)
            {
                // Shop sits between Pier and River in the recovered target order.
                model.handle_map_command(fh::MapCommand::NextTarget);
            }
            if(expected_pool == 4 || expected_pool == 5)
            {
                // Already on previous fishing target; one Next reaches the next area.
            }
            const fh::MapTarget target = model.selected_map_target();
            if(target == fh::MapTarget::Shop)
            {
                model.handle_map_command(fh::MapCommand::NextTarget);
            }
            model.handle_map_command(fh::MapCommand::Confirm);
            assert(model.state() == fh::GameState::Fishing);
            assert(model.fishing_pool() == expected_pool);
            model.handle_fishing_back();
        }
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.handle_map_command(fh::MapCommand::NextTarget); // Pier
        model.handle_map_command(fh::MapCommand::NextTarget); // Shop
        assert(model.selected_map_target() == fh::MapTarget::Shop);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Shop);
        model.handle_shop_back();
        assert(model.state() == fh::GameState::Map);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.catalog = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        // Catalog is the previous enabled target when only its purchase flag is unlocked.
        model.handle_map_command(fh::MapCommand::PreviousTarget);
        assert(model.selected_map_target() == fh::MapTarget::Catalog);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Catalog);
        model.handle_catalog_back(false);
        assert(model.state() == fh::GameState::Map);
    }


    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.money = 500;
        progress.bait_owned[2] = true;
        progress.character_owned[2] = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        const auto initial_revision = model.progress_revision();

        model.update_title_animation();
        assert(model.progress_revision() == initial_revision);
        model.handle_title_command(fh::TitleCommand::Play);
        model.update_map_markers();
        model.handle_map_command(fh::MapCommand::NextTarget);
        assert(model.progress_revision() == initial_revision);

        model.toggle_sound_option();
        assert(model.progress_revision() == initial_revision + 1);
        (void) model.cycle_owned_bait();
        assert(model.progress_revision() == initial_revision + 2);
        (void) model.cycle_owned_character();
        assert(model.progress_revision() == initial_revision + 3);

        const auto before_reward = model.progress_revision();
        model.apply_fishing_reward(1, 5);
        assert(model.progress_revision() == before_reward + 1);
        const auto before_duplicate_zero = model.progress_revision();
        model.apply_fishing_reward(1, 0);
        assert(model.progress_revision() == before_duplicate_zero);

        const auto before_purchase = model.progress_revision();
        assert(model.purchase_shop_item(0) == fh::ShopPurchaseResult::Purchased);
        assert(model.progress_revision() == before_purchase + 1);
        const auto before_sold_out = model.progress_revision();
        assert(model.purchase_shop_item(0) == fh::ShopPurchaseResult::SoldOut);
        assert(model.progress_revision() == before_sold_out);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = false;
        fh::FlowModel model(progress);
        model.complete_intro();
        const auto revision = model.progress_revision();
        model.handle_title_command(fh::TitleCommand::Play);
        model.complete_event();
        assert(model.progress_revision() == revision + 1);
        assert(model.progress_state().prologue_complete);
    }


    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.club_card = true;
        progress.old_boat = true;
        progress.ancient_map = true;
        progress.catalog = true;
        progress.captains_hat = true;
        progress.beach_ball = true;
        progress.character_owned = {true, true, true, false, false, false};
        progress.current_character = 0;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);

        // Character cycling is directional and skips locked characters.
        assert(model.cycle_owned_character(1) == 1);
        assert(model.cycle_owned_character(-1) == 0);
        assert(model.cycle_owned_character(-1) == 2);
        assert(model.cycle_owned_character(1) == 0);

        // Spatial map navigation follows the visible map graph, not a flat list.
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
        model.handle_map_command(fh::MapCommand::Left);
        assert(model.selected_map_target() == fh::MapTarget::Shop);
        model.handle_map_command(fh::MapCommand::Down);
        assert(model.selected_map_target() == fh::MapTarget::Lagoon);
        model.handle_map_command(fh::MapCommand::Down);
        assert(model.selected_map_target() == fh::MapTarget::Pier);
        model.handle_map_command(fh::MapCommand::Left);
        assert(model.selected_map_target() == fh::MapTarget::Cave);
        model.handle_map_command(fh::MapCommand::Down);
        assert(model.selected_map_target() == fh::MapTarget::Ocean);
        model.handle_map_command(fh::MapCommand::Up);
        assert(model.selected_map_target() == fh::MapTarget::Pier);
        model.handle_map_command(fh::MapCommand::Right);
        assert(model.selected_map_target() == fh::MapTarget::Beach);
        model.handle_map_command(fh::MapCommand::Up);
        assert(model.selected_map_target() == fh::MapTarget::River);
        model.handle_map_command(fh::MapCommand::Left);
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);

        // Catalog is a START shortcut, not a map selection target.
        model.open_catalog_from_map();
        assert(model.state() == fh::GameState::Catalog);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.catalog = false;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.open_catalog_from_map();
        assert(model.state() == fh::GameState::Map);

        // Locked spatial neighbors don't become selectable.
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
        model.handle_map_command(fh::MapCommand::Right); // River is locked.
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.club_card = true;
        progress.old_boat = true;
        progress.ancient_map = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);

        // Custom spots are purchase-gated: Captain's Hat -> Lagoon,
        // Beach Ball -> Beach, and Old Boat -> Ocean + Waterfall.
        assert(! model.map_target_enabled(fh::MapTarget::Lagoon));
        assert(! model.map_target_enabled(fh::MapTarget::Beach));
        assert(model.map_target_enabled(fh::MapTarget::Waterfall));

        fh::ProgressState custom_progress = progress;
        custom_progress.captains_hat = true;
        custom_progress.beach_ball = true;
        fh::FlowModel custom_model(custom_progress);
        custom_model.complete_intro();
        custom_model.handle_title_command(fh::TitleCommand::Play);
        assert(custom_model.map_target_enabled(fh::MapTarget::Lagoon));
        assert(custom_model.map_target_enabled(fh::MapTarget::Beach));
        assert(custom_model.map_target_enabled(fh::MapTarget::Waterfall));

        // Lagoon sits between Shop / Crystal Lake / Cave / Pier.
        custom_model.handle_map_command(fh::MapCommand::Left);
        assert(custom_model.selected_map_target() == fh::MapTarget::Shop);
        custom_model.handle_map_command(fh::MapCommand::Down);
        assert(custom_model.selected_map_target() == fh::MapTarget::Lagoon);
        custom_model.handle_map_command(fh::MapCommand::Right);
        assert(custom_model.selected_map_target() == fh::MapTarget::CrystalLake);
        custom_model.handle_map_command(fh::MapCommand::Left);
        custom_model.handle_map_command(fh::MapCommand::Down);
        custom_model.handle_map_command(fh::MapCommand::Down);
        assert(custom_model.selected_map_target() == fh::MapTarget::Pier);

        // Beach and Waterfall extend the southeast branch of the map graph.
        custom_model.handle_map_command(fh::MapCommand::Right);
        assert(custom_model.selected_map_target() == fh::MapTarget::Beach);
        custom_model.handle_map_command(fh::MapCommand::Down);
        assert(custom_model.selected_map_target() == fh::MapTarget::Waterfall);
        custom_model.handle_map_command(fh::MapCommand::Left);
        assert(custom_model.selected_map_target() == fh::MapTarget::Ocean);
        custom_model.handle_map_command(fh::MapCommand::Right);
        assert(custom_model.selected_map_target() == fh::MapTarget::Waterfall);
        custom_model.handle_map_command(fh::MapCommand::Right);
        assert(custom_model.selected_map_target() == fh::MapTarget::Beach);
        custom_model.handle_map_command(fh::MapCommand::Up);
        assert(custom_model.selected_map_target() == fh::MapTarget::River);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.club_card = true;
        progress.old_boat = true;
        progress.ancient_map = true;
        progress.captains_hat = true;
        progress.beach_ball = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);

        // Lagoon is the first fully playable custom fishing spot.
        model.handle_map_command(fh::MapCommand::Left);
        model.handle_map_command(fh::MapCommand::Down);
        assert(model.selected_map_target() == fh::MapTarget::Lagoon);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Fishing);
        assert(model.fishing_pool() == 6);

        // Beach and Waterfall remain map-only until their own art/content land.
        fh::FlowModel beach_model(progress);
        beach_model.complete_intro();
        beach_model.handle_title_command(fh::TitleCommand::Play);
        beach_model.handle_map_command(fh::MapCommand::Left);
        beach_model.handle_map_command(fh::MapCommand::Down);
        beach_model.handle_map_command(fh::MapCommand::Down);
        beach_model.handle_map_command(fh::MapCommand::Right);
        assert(beach_model.selected_map_target() == fh::MapTarget::Beach);
        beach_model.handle_map_command(fh::MapCommand::Confirm);
        assert(beach_model.state() == fh::GameState::Map);
        assert(beach_model.fishing_pool() == 0);

        fh::FlowModel waterfall_model(progress);
        waterfall_model.complete_intro();
        waterfall_model.handle_title_command(fh::TitleCommand::Play);
        waterfall_model.handle_map_command(fh::MapCommand::Left);
        waterfall_model.handle_map_command(fh::MapCommand::Down);
        waterfall_model.handle_map_command(fh::MapCommand::Down);
        waterfall_model.handle_map_command(fh::MapCommand::Right);
        waterfall_model.handle_map_command(fh::MapCommand::Down);
        assert(waterfall_model.selected_map_target() == fh::MapTarget::Waterfall);
        waterfall_model.handle_map_command(fh::MapCommand::Confirm);
        assert(waterfall_model.state() == fh::GameState::Map);
        assert(waterfall_model.fishing_pool() == 0);
    }
}


// ---- test_intro_model.cpp ----
#include <cassert>

#include "flow_model.h"
#include "intro_model.h"

void test_intro_model_contract()
{
    fh::ProgressState progress;
    fh::FlowModel flow(progress);
    assert(flow.state() == fh::GameState::Intro);

    fh::IntroModel intro;
    assert(! intro.done());
    assert(intro.ticks() == 0);

    for(int frame = 1; frame < 25; ++frame)
    {
        assert(intro.update() == fh::IntroEvent::None);
    }
    assert(intro.ticks() == 24);
    assert(intro.update() == fh::IntroEvent::FadeInAndSound);
    assert(intro.ticks() == 25);

    while(intro.ticks() < 174)
    {
        assert(intro.update() == fh::IntroEvent::None);
    }
    assert(intro.update() == fh::IntroEvent::FadeOut);
    assert(intro.ticks() == 175);

    while(! intro.done())
    {
        const fh::IntroEvent event = intro.update();
        assert(event == fh::IntroEvent::None || event == fh::IntroEvent::Complete);
    }
    assert(intro.ticks() == 192);
    intro.complete(flow);
    assert(flow.state() == fh::GameState::Title);

    {
        fh::ProgressState fresh;
        fh::FlowModel skipped_flow(fresh);
        fh::IntroModel skipped_intro;
        assert(skipped_flow.state() == fh::GameState::Intro);
        skipped_intro.skip(skipped_flow);
        assert(skipped_intro.done());
        assert(skipped_flow.state() == fh::GameState::Title);
    }
}


// ---- test_ui_font.cpp ----
#include <cassert>
#include "ui_font.h"

void test_ui_font_contract()
{
    using fh::ui_font_glyph;
    assert(ui_font_glyph('0') == 0);
    assert(ui_font_glyph('9') == 9);
    assert(ui_font_glyph('a') == 16);
    assert(ui_font_glyph('A') == 17);
    assert(ui_font_glyph('z') == 66);
    assert(ui_font_glyph('Z') == 67);
    assert(ui_font_glyph('.') == 68);
    assert(ui_font_glyph(',') == 69);
    assert(ui_font_glyph('!') == 70);
    assert(ui_font_glyph('?') == 71);
    assert(ui_font_glyph(':') == 72);
    assert(ui_font_glyph('<') == 73);
    assert(ui_font_glyph('-') == 74);
    assert(ui_font_glyph(' ') == -1);
    assert(ui_font_glyph('#') == -1);
}


// ---- test_options_model.cpp ----
#include <cassert>

#include "flow_model.h"
#include "options_model.h"

void test_options_model_contract()
{
    {
        fh::ProgressState progress;
        fh::FlowModel flow(progress);
        fh::OptionsModel options;
        assert(options.sound(flow) == 1);
        options.toggle_sound(flow);
        assert(options.sound(flow) == 0);
        options.toggle_sound(flow);
        assert(options.sound(flow) == 1);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel flow(progress);
        flow.complete_intro();
        flow.handle_title_command(fh::TitleCommand::Options);
        assert(flow.state() == fh::GameState::Options);
        fh::OptionsModel options;
        options.back(flow);
        assert(flow.state() == fh::GameState::Title);
    }
}


// ---- test_presentation_effects.cpp ----
#include <cassert>

#include "presentation_effects.h"

void test_presentation_effects_contract()
{
    using fh::PresentationColor;
    using fh::PresentationEffects;
    using fh::PresentationMode;

    PresentationEffects effects;
    assert(effects.mode() == PresentationMode::None);
    assert(effects.alpha() == 255);
    assert((effects.color() == PresentationColor{25, 5, 36}));
    assert(effects.black_screen());

    effects.start_fade_in();
    assert(effects.mode() == PresentationMode::FadeIn);
    assert(effects.black_screen());
    for(int index = 0; index < 16; ++index)
    {
        effects.update();
        assert(effects.mode() == PresentationMode::FadeIn);
        assert(effects.black_screen());
    }
    effects.update();
    assert(effects.mode() == PresentationMode::None);
    assert(effects.alpha() == 0);
    assert(! effects.black_screen());

    effects.start_fade_out();
    assert(effects.mode() == PresentationMode::FadeOut);
    for(int index = 0; index < 16; ++index)
    {
        effects.update();
        assert(! effects.black_screen());
    }
    effects.update();
    assert(effects.mode() == PresentationMode::None);
    assert(effects.alpha() == 255);
    assert(effects.black_screen());

    effects.start_fade_in();
    for(int index = 0; index < 17; ++index)
    {
        effects.update();
    }
    assert(effects.alpha() == 0);

    effects.start_flash();
    assert(effects.mode() == PresentationMode::FlashIn);
    assert((effects.color() == PresentationColor{235, 255, 237}));
    effects.update();
    assert(effects.alpha() == 150);
    assert(effects.mode() == PresentationMode::FlashIn);
    effects.update();
    assert(effects.alpha() == 255);
    assert(effects.mode() == PresentationMode::FlashOut);
    assert(effects.flash_ticks() == 0);

    for(int index = 0; index < 3; ++index)
    {
        effects.update();
        assert(effects.alpha() == 255);
        assert(effects.mode() == PresentationMode::FlashOut);
    }
    effects.update();
    assert(effects.alpha() == 105);
    effects.update();
    assert(effects.alpha() == 0);
    assert(effects.mode() == PresentationMode::None);
    assert((effects.color() == PresentationColor{25, 5, 36}));
    assert(effects.flash_ticks() == 0);
}


// ---- test_save_codec.cpp ----
#include <cassert>
#include <cstdint>

#include "save_codec.h"

namespace
{

void assert_progress_equal(const fh::ProgressState& a, const fh::ProgressState& b)
{
    assert(a.prologue_complete == b.prologue_complete);
    assert(a.sound == b.sound);
    assert(a.club_card == b.club_card);
    assert(a.old_boat == b.old_boat);
    assert(a.ancient_map == b.ancient_map);
    assert(a.catalog == b.catalog);
    assert(a.captains_hat == b.captains_hat);
    assert(a.beach_ball == b.beach_ball);
    assert(a.money == b.money);
    assert(a.current_character == b.current_character);
    assert(a.current_rod == b.current_rod);
    assert(a.equipped_bait == b.equipped_bait);
    assert(a.bait_owned == b.bait_owned);
    assert(a.rod_owned == b.rod_owned);
    assert(a.character_owned == b.character_owned);
    assert(a.fish_catalog == b.fish_catalog);
}

}

void test_save_codec_contract()
{
    const fh::ProgressState defaults = fh::canonical_default_progress();
    assert(defaults.money == 10);
    assert(defaults.sound == 1);
    assert(! defaults.prologue_complete);
    assert(defaults.bait_owned[0]);
    assert(defaults.rod_owned[0]);
    assert(defaults.character_owned[0]);
    assert(defaults.character_owned[1]);

    const fh::SaveImage fresh = fh::encode_save(defaults);
    static_assert(fh::SAVE_IMAGE_SIZE == 32);
    assert(fresh.bytes[0] == 'F');
    assert(fresh.bytes[1] == 'H');
    assert(fresh.bytes[2] == 'G');
    assert(fresh.bytes[3] == 'S');
    static_assert(fh::SAVE_FORMAT_VERSION == 2);
    static_assert(fh::SAVE_PAYLOAD_SIZE == 19);
    assert(fresh.bytes[4] == 2 && fresh.bytes[5] == 0);  // version 2 LE
    assert(fresh.bytes[6] == 19 && fresh.bytes[7] == 0); // payload bytes LE

    fh::SaveImage old_v1 = fresh;
    old_v1.bytes[4] = 1;
    old_v1.bytes[5] = 0;
    assert(! fh::decode_save(old_v1).valid);

    const fh::SaveDecodeResult fresh_decoded = fh::decode_save(fresh);
    assert(fresh_decoded.valid);
    assert_progress_equal(defaults, fresh_decoded.progress);
    assert(! fresh_decoded.progress.captains_hat);
    assert(! fresh_decoded.progress.beach_ball);

    fh::ProgressState full = defaults;
    full.prologue_complete = true;
    full.sound = 0;
    full.club_card = true;
    full.old_boat = true;
    full.ancient_map = true;
    full.catalog = true;
    full.captains_hat = true;
    full.beach_ball = true;
    full.money = 987;
    full.current_character = 5;
    full.current_rod = 2;
    full.equipped_bait = 6;
    full.bait_owned.fill(true);
    full.rod_owned.fill(true);
    full.character_owned.fill(true);
    for(int index = 0; index < 44; ++index)
    {
        full.fish_catalog[index] = index % 3 != 1;
    }

    const fh::SaveImage full_image_a = fh::encode_save(full);
    const fh::SaveImage full_image_b = fh::encode_save(full);
    assert(full_image_a.bytes == full_image_b.bytes);
    assert((full_image_a.bytes[22] & 0x30u) == 0x30u);
    const fh::SaveDecodeResult full_decoded = fh::decode_save(full_image_a);
    assert(full_decoded.valid);
    assert_progress_equal(full, full_decoded.progress);

    fh::SaveImage corrupt = full_image_a;
    corrupt.bytes[15] ^= 0x40;
    const fh::SaveDecodeResult corrupt_decoded = fh::decode_save(corrupt);
    assert(! corrupt_decoded.valid);
    assert_progress_equal(defaults, corrupt_decoded.progress);

    fh::SaveImage wrong_version = full_image_a;
    wrong_version.bytes[4] = 3;
    const fh::SaveDecodeResult version_decoded = fh::decode_save(wrong_version);
    assert(! version_decoded.valid);
    assert_progress_equal(defaults, version_decoded.progress);

    fh::SaveImage bad_ranges = full_image_a;
    // Payload begins at 12. Corrupt range fields then recompute CRC through the public helper path
    // by decoding a deliberately encoded out-of-range source ProgressState instead.
    fh::ProgressState invalid_source = defaults;
    invalid_source.sound = 99;
    invalid_source.money = 5000;
    invalid_source.current_character = 99;
    invalid_source.current_rod = 99;
    invalid_source.equipped_bait = 99;
    invalid_source.bait_owned.fill(false);
    invalid_source.rod_owned.fill(false);
    invalid_source.character_owned.fill(false);
    const fh::SaveDecodeResult sanitized = fh::decode_save(fh::encode_save(invalid_source));
    assert(sanitized.valid);
    assert(sanitized.progress.sound == 1);
    assert(sanitized.progress.money == 999);
    assert(sanitized.progress.bait_owned[0]);
    assert(sanitized.progress.rod_owned[0]);
    assert(sanitized.progress.character_owned[0]);
    assert(sanitized.progress.character_owned[1]);
    assert(sanitized.progress.current_character == 0);
    assert(sanitized.progress.current_rod == 0);
    assert(sanitized.progress.equipped_bait == 0);
}


// ---- test_shop_model.cpp ----
#include <array>
#include <cassert>

#include "flow_model.h"
#include "progression_content.h"
#include "shop_model.h"

namespace
{

constexpr std::array<int, 18> EXPECTED_PRICES = {
    15, 15, 30, 45, 100, 100, 45, 120, 30, 60, 120, 20, 30, 30, 50, 100, 60, 30,
};

void verify_effect(int slot, const fh::FlowModel& flow)
{
    if(slot <= 5)
    {
        assert(flow.bait_owned(slot + 1));
        return;
    }

    switch(slot)
    {
    case 6:
        assert(flow.rod_owned(1));
        assert(flow.current_rod() == 1);
        break;
    case 7:
        assert(flow.rod_owned(2));
        assert(flow.current_rod() == 2);
        break;
    case 8:
        assert(flow.map_target_enabled(fh::MapTarget::Ocean));
        assert(flow.map_target_enabled(fh::MapTarget::Waterfall));
        break;
    case 9:
        assert(flow.map_target_enabled(fh::MapTarget::River));
        break;
    case 10:
        assert(flow.map_target_enabled(fh::MapTarget::Cave));
        break;
    case 11:
        assert(flow.map_target_enabled(fh::MapTarget::Catalog));
        break;
    case 12:
        assert(flow.character_owned(2));
        break;
    case 13:
        assert(flow.character_owned(3));
        break;
    case 14:
        assert(flow.character_owned(4));
        break;
    case 15:
        assert(flow.character_owned(5));
        break;
    case 16:
        assert(flow.map_target_enabled(fh::MapTarget::Lagoon));
        break;
    case 17:
        assert(flow.map_target_enabled(fh::MapTarget::Beach));
        break;
    default:
        assert(false);
    }
}

}

void test_shop_model_contract()
{
    assert(fh::shop_item_count() == 18);
    for(int slot = 0; slot < 18; ++slot)
    {
        const fh::ShopItemSpec* item = fh::shop_item_spec(slot);
        assert(item);
        assert(item->slot == slot);
        assert(item->price == EXPECTED_PRICES[slot]);
        assert(item->name && item->name[0] != '\0');
        assert(item->description && item->description[0] != '\0');
    }
    assert(fh::shop_item_spec(-1) == nullptr);
    assert(fh::shop_item_spec(18) == nullptr);

    {
        fh::ProgressState progress;
        assert(progress.money == 10);
        assert(progress.sound == 1);
        assert(progress.current_character == 0);
        assert((progress.rod_owned == std::array<bool, 3>{true, false, false}));
        assert((progress.character_owned == std::array<bool, 6>{true, true, false, false, false, false}));
    }

    for(int slot = 0; slot < 18; ++slot)
    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.money = 999;
        fh::FlowModel flow(progress);
        if(slot == 7)
        {
            assert(flow.purchase_shop_item(6) == fh::ShopPurchaseResult::Purchased);
        }
        fh::ShopModel shop;
        shop.select(slot);

        assert(shop.selected_item() == slot);
        assert(shop.price() == EXPECTED_PRICES[slot]);
        assert(! shop.sold_out(flow));
        const int before = flow.money();
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::Purchased);
        assert(flow.money() == before - EXPECTED_PRICES[slot]);
        assert(shop.sold_out(flow));
        verify_effect(slot, flow);

        const int after = flow.money();
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::SoldOut);
        assert(flow.money() == after);
    }

    {
        fh::ProgressState progress;
        progress.money = 14;
        fh::FlowModel flow(progress);
        fh::ShopModel shop;
        shop.select(0);
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::InsufficientFunds);
        assert(flow.money() == 14);
        assert(! flow.bait_owned(1));
    }

    {
        fh::ShopModel shop;
        assert(shop.selected_item() == 0);
        assert(shop.page() == 0);
        shop.previous();
        assert(shop.selected_item() == 17);
        assert(shop.page() == 1);
        shop.next();
        assert(shop.selected_item() == 0);
        shop.select(17);
        shop.next();
        assert(shop.selected_item() == 0);
        shop.select(-1);
        assert(shop.selected_item() == 0);
        shop.select(18);
        assert(shop.selected_item() == 0);

        // Shoulder-page navigation keeps the original 4x4 page intact and
        // exposes only the two active cells on custom page 2.
        shop.next_page();
        assert(shop.page() == 1);
        assert(shop.selected_item() == 16);
        shop.move_right();
        assert(shop.selected_item() == 17);
        shop.move_right();
        assert(shop.selected_item() == 17);
        shop.move_down();
        assert(shop.selected_item() == 17);
        shop.move_up();
        assert(shop.selected_item() == 13);
        assert(shop.page() == 0);
        shop.move_down();
        assert(shop.selected_item() == 17);
        assert(shop.page() == 1);
        shop.move_left();
        assert(shop.selected_item() == 16);
        shop.move_up();
        assert(shop.selected_item() == 12);
        assert(shop.page() == 0);
        shop.move_down();
        assert(shop.selected_item() == 16);
        assert(shop.page() == 1);
        shop.previous_page();
        assert(shop.page() == 0);
        assert(shop.selected_item() == 0);
    }

    {
        // D-pad navigation follows the 4x4 page grid and crosses naturally
        // between pages at the top/bottom edge. A partial target row clamps to
        // its nearest populated item.
        fh::ShopModel shop;
        assert(shop.selected_item() == 0);
        shop.move_left();
        assert(shop.selected_item() == 0);
        shop.move_up();
        assert(shop.selected_item() == 0);

        shop.move_right();
        assert(shop.selected_item() == 1);
        shop.move_down();
        assert(shop.selected_item() == 5);
        shop.move_down();
        assert(shop.selected_item() == 9);
        shop.move_down();
        assert(shop.selected_item() == 13);
        shop.move_down();
        assert(shop.selected_item() == 17);
        assert(shop.page() == 1);
        shop.move_up();
        assert(shop.selected_item() == 13);
        assert(shop.page() == 0);

        const int expected_page_two[4] = {16, 17, 17, 17};
        const int expected_page_one[2] = {12, 13};
        for(int column = 0; column < 4; ++column)
        {
            shop.select(12 + column);
            shop.move_down();
            assert(shop.selected_item() == expected_page_two[column]);
            assert(shop.page() == 1);
        }
        for(int column = 0; column < 2; ++column)
        {
            shop.select(16 + column);
            shop.move_up();
            assert(shop.selected_item() == expected_page_one[column]);
            assert(shop.page() == 0);
        }

        shop.select(3);
        shop.move_right();
        assert(shop.selected_item() == 3);
        shop.select(15);
        shop.move_right();
        assert(shop.selected_item() == 15);
    }

    {
        fh::ProgressState progress;
        progress.money = 999;
        fh::FlowModel flow(progress);
        assert(flow.current_character() == 0);
        assert(flow.character_owned(0));
        assert(flow.character_owned(1));
        for(int character = 2; character < 6; ++character)
        {
            assert(! flow.character_owned(character));
        }
        assert(flow.cycle_owned_character() == 1);
        assert(flow.cycle_owned_character() == 0);

        assert(flow.purchase_shop_item(12) == fh::ShopPurchaseResult::Purchased);
        assert(flow.cycle_owned_character() == 1);
        assert(flow.cycle_owned_character() == 2);
        assert(flow.cycle_owned_character() == 0);
    }

    {
        // The original Shop hides Nova Rod until Pro Rod has been bought.
        fh::ProgressState progress;
        progress.money = 999;
        fh::FlowModel flow(progress);
        fh::ShopModel shop;
        shop.select(7);
        assert(flow.shop_item_locked(7));
        assert(! flow.shop_item_purchasable(7));
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::Locked);
        assert(! flow.rod_owned(2));

        shop.select(6);
        assert(flow.shop_item_purchasable(6));
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::Purchased);
        assert(! flow.shop_item_locked(7));
        assert(flow.shop_item_purchasable(7));
        shop.select(7);
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::Purchased);
        assert(flow.rod_owned(2));
    }

    {
        // Secret Shop-only Konami tracker: Up Up Down Down Left Right Left Right B A.
        // It must finish within 300 frames (5 seconds at 60 Hz).
        fh::ShopModel shop;
        using Key = fh::ShopCheatKey;
        using Result = fh::ShopCheatResult;
        assert(shop.push_cheat_key(Key::Up, 10) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Up, 20) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Down, 30) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Down, 40) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Left, 50) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Right, 60) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Left, 70) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Right, 80) == Result::Progressed);
        assert(shop.push_cheat_key(Key::B, 90) == Result::Progressed);
        assert(shop.push_cheat_key(Key::A, 100) == Result::Completed);

        // Completion resets the sequence.
        assert(shop.push_cheat_key(Key::A, 101) == Result::NoProgress);

        // Timeout resets the sequence, but a new Up can immediately restart it.
        assert(shop.push_cheat_key(Key::Up, 200) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Up, 501) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Down, 502) == Result::NoProgress);

        // Wrong keys reset; Up itself can become a fresh prefix.
        assert(shop.push_cheat_key(Key::Up, 600) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Right, 601) == Result::NoProgress);
        assert(shop.push_cheat_key(Key::Up, 602) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Up, 603) == Result::Progressed);
    }

    {
        // Cheat reward uses the same progress revision/save path as real progression.
        fh::ProgressState progress;
        progress.money = 10;
        fh::FlowModel flow(progress);
        const auto revision = flow.progress_revision();
        flow.grant_money(30);
        assert(flow.money() == 40);
        assert(flow.progress_revision() == revision + 1);
        flow.grant_money(1000);
        assert(flow.money() == 999);
        const auto capped_revision = flow.progress_revision();
        flow.grant_money(30);
        assert(flow.money() == 999);
        assert(flow.progress_revision() == capped_revision);
        flow.grant_money(-1);
        assert(flow.money() == 999);
    }
}


int main()
{
    test_audio_policy_contract();
    test_catalog_model_contract();
    test_dialog_model_contract();
    test_event_model_contract();
    test_fishing_content_contract();
    test_fishing_model_contract();
    test_flow_model_contract();
    test_intro_model_contract();
    test_ui_font_contract();
    test_options_model_contract();
    test_presentation_effects_contract();
    test_save_codec_contract();
    test_shop_model_contract();
    return 0;
}
