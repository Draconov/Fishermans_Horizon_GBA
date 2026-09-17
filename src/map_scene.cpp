#include "map_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_map_bg.h"
#include "bn_regular_bg_items_map_bg_region2.h"
#include "bn_sprite_items_ui_font.h"
#include "bn_sprite_items_shop_cursor.h"
#include "bn_sprite_items_map_catalog_parts.h"
#include "bn_sprite_items_map_character_0.h"
#include "bn_sprite_items_map_character_1.h"
#include "bn_sprite_items_map_character_2.h"
#include "bn_sprite_items_map_character_3.h"
#include "bn_sprite_items_map_character_4.h"
#include "bn_sprite_items_map_character_5.h"
#include "bn_sprite_items_map_spots.h"
#include "bn_sprite_items_map_travel_spots.h"

#include "flow_model.h"
#include "ui_font.h"
#include "ui_text_layout.h"

namespace fh
{
namespace
{

constexpr const char* CHARACTER_NAMES[] = {"Cid", "Fran", "Leon", "Sazh", "Rosa", "Shadow"};

bn::regular_bg_ptr create_map_background(Region region)
{
    if(region == Region::CoastalCity)
    {
        return bn::regular_bg_items::map_bg_region2.create_bg(0, 0);
    }
    return bn::regular_bg_items::map_bg.create_bg(0, 0);
}

bn::sprite_ptr create_selection_cursor(Region region)
{
    const MapTargetSpec* spec = map_target_spec(region_first_target(region));
    const int x = spec ? spec->screen_x + 4 - 120 : 36;
    const int y = spec ? spec->screen_y + 4 - 80 : -48;
    return bn::sprite_items::shop_cursor.create_sprite(x, y, 0);
}

void append_text(bn::vector<bn::sprite_ptr, 24>& sprites, const char* text, int screen_x, int screen_y, int max_chars)
{
    int pen_x = 0;
    int count = 0;
    while(*text && count < max_chars && sprites.size() < sprites.max_size())
    {
        const char character = *text++;
        if(character == '#') break;
        const int glyph = ui_font_glyph(character);
        if(glyph >= 0)
        {
            sprites.push_back(bn::sprite_items::ui_font.create_sprite(
                screen_x + pen_x + ui_character_draw_x_adjust(character) + 4 - 120,
                screen_y + 4 - 80, glyph));
        }
        pen_x += ui_character_advance(character);
        ++count;
    }
}

}

MapScene::MapScene(Region region) :
    _region(region),
    _background(create_map_background(region)),
    _character(bn::sprite_items::map_character_0.create_sprite(79, 43, 0)),
    _selection_cursor(create_selection_cursor(region))
{
    _build_markers();

    if(_region == Region::MariMari)
    {
        for(int part = 0; part < 3; ++part)
        {
            bn::sprite_ptr sprite = bn::sprite_items::map_catalog_parts.create_sprite(-104 + part * 32, 72, part);
            sprite.set_visible(false);
            _catalog_parts.push_back(bn::move(sprite));
        }
    }
}

Region MapScene::region() const noexcept
{
    return _region;
}

void MapScene::_build_markers()
{
    const int count = region_target_count(_region);
    for(int index = 0; index < count; ++index)
    {
        const MapTarget target = region_target_at(_region, index);
        const MapTargetSpec* spec = map_target_spec(target);
        if(! spec || spec->marker_kind == MapMarkerKind::Catalog)
        {
            continue;
        }

        bn::sprite_ptr sprite = spec->marker_kind == MapMarkerKind::Travel ?
            bn::sprite_items::map_travel_spots.create_sprite(spec->screen_x - 120, spec->screen_y - 80, 0) :
            bn::sprite_items::map_spots.create_sprite(
                spec->screen_x - 120, spec->screen_y - 80,
                spec->marker_kind == MapMarkerKind::Shop ? 2 : 0);
        sprite.set_visible(false);
        _marker_sprites.push_back(bn::move(sprite));
        _marker_targets.push_back(target);
        _marker_kinds.push_back(spec->marker_kind);
    }
}

void MapScene::update(FlowModel& flow)
{
    if(bn::keypad::b_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::Back);
    }
    else if(bn::keypad::start_pressed())
    {
        if(flow.progress_state().catalog)
        {
            _audio_event = AudioCue::NextPage;
            flow.open_catalog_from_map();
        }
    }
    else if(bn::keypad::left_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::Left);
    }
    else if(bn::keypad::right_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::Right);
    }
    else if(bn::keypad::up_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::Up);
    }
    else if(bn::keypad::down_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::Down);
    }
    else if(bn::keypad::l_pressed())
    {
        _audio_event = AudioCue::NextPage;
        (void) flow.cycle_owned_character(-1);
    }
    else if(bn::keypad::r_pressed())
    {
        _audio_event = AudioCue::NextPage;
        (void) flow.cycle_owned_character(1);
    }
    else if(bn::keypad::a_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::Confirm);
    }

    if(flow.state() != GameState::Map || flow.active_region() != _region)
    {
        return;
    }

    flow.update_map_markers();
    _update_marker_graphics(flow);
    _update_marker_visibility(flow);
    _update_character(flow);
    _update_selection(flow);
    _update_catalog(flow);
    _update_text(flow);
}

void MapScene::_update_marker_graphics(const FlowModel& flow)
{
    const int next_a_index = flow.map_spot_a_tile() - 100;
    const int next_b_index = flow.map_spot_b_tile() - 100;
    if(next_a_index == _spot_a_graphics_index && next_b_index == _spot_b_graphics_index)
    {
        return;
    }

    _spot_a_graphics_index = next_a_index;
    _spot_b_graphics_index = next_b_index;
    for(int index = 0; index < int(_marker_sprites.size()); ++index)
    {
        switch(_marker_kinds[index])
        {
        case MapMarkerKind::Fishing:
            _marker_sprites[index].set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
            break;
        case MapMarkerKind::Shop:
            _marker_sprites[index].set_tiles(bn::sprite_items::map_spots.tiles_item(), next_b_index);
            break;
        case MapMarkerKind::Travel:
            _marker_sprites[index].set_tiles(bn::sprite_items::map_travel_spots.tiles_item(), next_a_index);
            break;
        case MapMarkerKind::Catalog:
            break;
        }
    }
}

void MapScene::_update_marker_visibility(const FlowModel& flow)
{
    for(int index = 0; index < int(_marker_sprites.size()); ++index)
    {
        _marker_sprites[index].set_visible(flow.map_target_enabled(_marker_targets[index]));
    }
}

void MapScene::_update_character(const FlowModel& flow)
{
    const int character = flow.current_character();
    if(character == _last_character) return;
    _last_character = character;
    switch(character)
    {
    case 0: _character.set_item(bn::sprite_items::map_character_0); break;
    case 1: _character.set_item(bn::sprite_items::map_character_1); break;
    case 2: _character.set_item(bn::sprite_items::map_character_2); break;
    case 3: _character.set_item(bn::sprite_items::map_character_3); break;
    case 4: _character.set_item(bn::sprite_items::map_character_4); break;
    case 5: _character.set_item(bn::sprite_items::map_character_5); break;
    default:
        _last_character = 0;
        _character.set_item(bn::sprite_items::map_character_0);
        break;
    }
    _text_dirty = true;
}

void MapScene::_update_selection(const FlowModel& flow)
{
    const MapTarget selected = flow.selected_map_target();
    if(_has_last_target && selected == _last_target) return;
    const MapTargetSpec* spec = map_target_spec(selected);
    if(! spec || spec->region != _region) return;
    _last_target = selected;
    _has_last_target = true;
    _selection_cursor.set_position(spec->screen_x + 4 - 120, spec->screen_y + 4 - 80);
}

void MapScene::_update_catalog(const FlowModel& flow)
{
    if(_region != Region::MariMari) return;
    const bool visible = flow.map_target_enabled(MapTarget::Catalog);
    for(bn::sprite_ptr& sprite : _catalog_parts) sprite.set_visible(visible);
}

void MapScene::_update_text(const FlowModel& flow)
{
    if(! _text_dirty) return;
    _text_dirty = false;
    _text_sprites.clear();

    int character = flow.current_character();
    if(character < 0 || character >= 6) character = 0;
    const char* character_name = CHARACTER_NAMES[character];
    constexpr int field_x = 168;
    constexpr int field_width = 48;
    const int text_width = ui_text_width(character_name, 6);
    append_text(_text_sprites, character_name, field_x + (field_width - text_width) / 2, 144, 6);
}

AudioCue MapScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
