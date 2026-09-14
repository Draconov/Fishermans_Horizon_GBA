#include "map_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_map.h"
#include "bn_sprite_items_map_spots.h"

#include "flow_model.h"

namespace fh
{

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
    _cave_spot(bn::sprite_items::map_spots.create_sprite(-96, 20, 0))
{
}

void MapScene::update(FlowModel& flow)
{
    if(bn::keypad::b_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::Back);
    }
    else if(bn::keypad::left_pressed() || bn::keypad::up_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::PreviousTarget);
    }
    else if(bn::keypad::right_pressed() || bn::keypad::down_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_map_command(MapCommand::NextTarget);
    }
    else if(bn::keypad::l_pressed() || bn::keypad::r_pressed())
    {
        _audio_event = AudioCue::NextPage;
        (void) flow.cycle_owned_character();
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
        case MapTarget::Catalog:
            flow.handle_map_command(MapCommand::Confirm);
            break;
        }
    }

    if(flow.state() != GameState::Map)
    {
        return;
    }

    flow.update_map_markers();
    _update_marker_graphics(flow);
    _update_selection_visibility(flow);
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
    }

    const int next_b_index = flow.map_spot_b_tile() - 100;
    if(next_b_index != _spot_b_graphics_index)
    {
        _spot_b_graphics_index = next_b_index;
        _shop_spot.set_tiles(bn::sprite_items::map_spots.tiles_item(), next_b_index);
    }
}

void MapScene::_update_selection_visibility(const FlowModel& flow)
{
    _selection_ticks = (_selection_ticks + 1) % 16;
    const bool selected_visible = _selection_ticks < 10;
    const MapTarget selected = flow.selected_map_target();

    _crystal_spot.set_visible(selected != MapTarget::CrystalLake || selected_visible);
    _pier_spot.set_visible(selected != MapTarget::Pier || selected_visible);
    _shop_spot.set_visible(selected != MapTarget::Shop || selected_visible);
    _river_spot.set_visible(flow.map_target_enabled(MapTarget::River) &&
                            (selected != MapTarget::River || selected_visible));
    _ocean_spot.set_visible(flow.map_target_enabled(MapTarget::Ocean) &&
                            (selected != MapTarget::Ocean || selected_visible));
    _cave_spot.set_visible(flow.map_target_enabled(MapTarget::Cave) &&
                           (selected != MapTarget::Cave || selected_visible));
}



AudioCue MapScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
