#include "map_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_map.h"
#include "bn_sprite_items_m4_font.h"
#include "bn_sprite_items_m4_shop_cursor.h"
#include "bn_sprite_items_map_catalog_parts.h"
#include "bn_sprite_items_map_character_0.h"
#include "bn_sprite_items_map_character_1.h"
#include "bn_sprite_items_map_character_2.h"
#include "bn_sprite_items_map_character_3.h"
#include "bn_sprite_items_map_character_4.h"
#include "bn_sprite_items_map_character_5.h"
#include "bn_sprite_items_map_spots.h"

#include "flow_model.h"
#include "m4_font.h"
#include "m4_text_layout.h"

namespace fh
{
namespace
{

constexpr const char* CHARACTER_NAMES[] = {
    "Cid",
    "Fran",
    "Leon",
    "Sazh",
    "Rosa",
    "Shadow",
};

void append_text(bn::vector<bn::sprite_ptr, 24>& sprites, const char* text, int screen_x, int screen_y,
                 int max_chars)
{
    int pen_x = 0;
    int count = 0;
    while(*text && count < max_chars && sprites.size() < sprites.max_size())
    {
        const char character = *text++;
        if(character == '#')
        {
            break;
        }
        const int glyph = m4_font_glyph(character);
        if(glyph >= 0)
        {
            sprites.push_back(bn::sprite_items::m4_font.create_sprite(
                screen_x + pen_x + m4_character_draw_x_adjust(character) + 4 - 120,
                screen_y + 4 - 80, glyph));
        }
        pen_x += m4_character_advance(character);
        ++count;
    }
}


}

MapScene::MapScene() :
    _background(bn::regular_bg_items::map.create_bg(0, 0)),
    // Reference top-left (100,12), 8x16 -> Butano center (-16,-60).
    _shop_spot(bn::sprite_items::map_spots.create_sprite(-16, -60, 2)),
    // Reference top-left (148,20), 8x16 -> Butano center (32,-52).
    _crystal_spot(bn::sprite_items::map_spots.create_sprite(32, -52, 0)),
    // Reference top-left (132,76), 8x16 -> Butano center (16,4).
    _pier_spot(bn::sprite_items::map_spots.create_sprite(16, 4, 0)),
    // Reference top-left (212,12), 8x16 -> Butano center (96,-60).
    _river_spot(bn::sprite_items::map_spots.create_sprite(96, -60, 0)),
    // Reference top-left (108,124), 8x16 -> Butano center (-8,52).
    _ocean_spot(bn::sprite_items::map_spots.create_sprite(-8, 52, 0)),
    // Reference top-left (20,92), 8x16 -> Butano center (-96,20).
    _cave_spot(bn::sprite_items::map_spots.create_sprite(-96, 20, 0)),
    // New user-marked fishing spots reuse the normal animated marker art.
    _lagoon_spot(bn::sprite_items::map_spots.create_sprite(-33, -42, 0)),
    _beach_spot(bn::sprite_items::map_spots.create_sprite(46, 24, 0)),
    _waterfall_spot(bn::sprite_items::map_spots.create_sprite(18, 59, 0)),
    // Reference GameMap.draw top-left (183,91), 24x40 padded to 32x64.
    _character(bn::sprite_items::map_character_0.create_sprite(79, 43, 0)),
    // Default selection is Crystal Lake. Tile 165 is a 24x24 corner frame
    // padded to 32x32; this centers it around the 8x16 marker.
    _selection_cursor(bn::sprite_items::m4_shop_cursor.create_sprite(36, -48, 0))
{
    // Original tile 170 is an 80x24 Catalog badge at screen (0,136). It is
    // split into three 32x32 GBA sprites without scaling.
    for(int part = 0; part < 3; ++part)
    {
        bn::sprite_ptr sprite = bn::sprite_items::map_catalog_parts.create_sprite(-104 + part * 32, 72, part);
        sprite.set_visible(false);
        _catalog_parts.push_back(bn::move(sprite));
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
        if(flow.map_target_enabled(MapTarget::Catalog))
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
        switch(flow.selected_map_target())
        {
        case MapTarget::CrystalLake:
        case MapTarget::Pier:
        case MapTarget::River:
        case MapTarget::Ocean:
        case MapTarget::Cave:
        case MapTarget::Shop:
            flow.handle_map_command(MapCommand::Confirm);
            break;
        case MapTarget::Lagoon:
        case MapTarget::Beach:
        case MapTarget::Waterfall:
        case MapTarget::Catalog:
            break;
        }
    }

    if(flow.state() != GameState::Map)
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
    if(next_a_index != _spot_a_graphics_index)
    {
        _spot_a_graphics_index = next_a_index;
        _crystal_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
        _pier_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
        _river_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
        _ocean_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
        _cave_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
        _lagoon_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
        _beach_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
        _waterfall_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_a_index);
    }

    const int next_b_index = flow.map_spot_b_tile() - 100;
    if(next_b_index != _spot_b_graphics_index)
    {
        _spot_b_graphics_index = next_b_index;
        _shop_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_b_index);
    }
}

void MapScene::_update_marker_visibility(const FlowModel& flow)
{
    _crystal_spot.set_visible(true);
    _pier_spot.set_visible(true);
    _shop_spot.set_visible(true);
    _river_spot.set_visible(flow.map_target_enabled(MapTarget::River));
    _ocean_spot.set_visible(flow.map_target_enabled(MapTarget::Ocean));
    _cave_spot.set_visible(flow.map_target_enabled(MapTarget::Cave));
    _lagoon_spot.set_visible(flow.map_target_enabled(MapTarget::Lagoon));
    _beach_spot.set_visible(flow.map_target_enabled(MapTarget::Beach));
    _waterfall_spot.set_visible(flow.map_target_enabled(MapTarget::Waterfall));
}

void MapScene::_update_character(const FlowModel& flow)
{
    const int character = flow.current_character();
    if(character == _last_character)
    {
        return;
    }

    _last_character = character;
    switch(character)
    {
    case 0:
        _character.set_item(bn::sprite_items::map_character_0);
        break;
    case 1:
        _character.set_item(bn::sprite_items::map_character_1);
        break;
    case 2:
        _character.set_item(bn::sprite_items::map_character_2);
        break;
    case 3:
        _character.set_item(bn::sprite_items::map_character_3);
        break;
    case 4:
        _character.set_item(bn::sprite_items::map_character_4);
        break;
    case 5:
        _character.set_item(bn::sprite_items::map_character_5);
        break;
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
    if(_has_last_target && selected == _last_target)
    {
        return;
    }

    _last_target = selected;
    _has_last_target = true;

    switch(selected)
    {
    case MapTarget::CrystalLake:
        _selection_cursor.set_position(36, -48);
        break;
    case MapTarget::Pier:
        _selection_cursor.set_position(20, 8);
        break;
    case MapTarget::Shop:
        _selection_cursor.set_position(-12, -56);
        break;
    case MapTarget::River:
        _selection_cursor.set_position(100, -56);
        break;
    case MapTarget::Ocean:
        _selection_cursor.set_position(-4, 56);
        break;
    case MapTarget::Cave:
        _selection_cursor.set_position(-92, 24);
        break;
    case MapTarget::Lagoon:
        _selection_cursor.set_position(-29, -38);
        break;
    case MapTarget::Beach:
        _selection_cursor.set_position(50, 28);
        break;
    case MapTarget::Waterfall:
        _selection_cursor.set_position(22, 63);
        break;
    case MapTarget::Catalog:
        _selection_cursor.set_position(-104, 72);
        break;
    }
}

void MapScene::_update_catalog(const FlowModel& flow)
{
    const bool visible = flow.map_target_enabled(MapTarget::Catalog);
    for(bn::sprite_ptr& sprite : _catalog_parts)
    {
        sprite.set_visible(visible);
    }
}

void MapScene::_update_text(const FlowModel& flow)
{
    if(! _text_dirty)
    {
        return;
    }
    _text_dirty = false;
    _text_sprites.clear();

    int character = flow.current_character();
    if(character < 0 || character >= 6)
    {
        character = 0;
    }
    const char* character_name = CHARACTER_NAMES[character];
    constexpr int field_x = 168;
    constexpr int field_width = 48;
    const int text_width = m4_text_width(character_name, 6);
    append_text(_text_sprites, character_name, field_x + (field_width - text_width) / 2, 144, 6);

}

AudioCue MapScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
