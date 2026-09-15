#include "catalog_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_m4_catalog_anim.h"
#include "bn_sprite_items_fishing_fish_m3_0.h"
#include "bn_sprite_items_fishing_fish_m3_1.h"
#include "bn_sprite_items_m4_catalog_cursor.h"
#include "bn_sprite_items_m4_font.h"

#include "catalog_model.h"
#include "fishing_content.h"
#include "flow_model.h"
#include "m4_font.h"
#include "m4_text_layout.h"

namespace fh
{
namespace
{

int fish_source_sprite(int fish_number)
{
    for(int pool = 1; pool <= fishing_area_count(); ++pool)
    {
        const FishingAreaSpec& area = fishing_area_spec(pool);
        for(const FishSpec& fish : area.fish)
        {
            if(fish.number == fish_number)
            {
                return fish.sprite;
            }
        }
    }
    return -1;
}

int m3_fish_bank(int source_sprite)
{
    switch(source_sprite)
    {
    case 110: case 111: case 120: case 121: case 122: case 123: case 126: case 127:
    case 129: case 130: case 131: case 132: case 133: case 134: case 135: case 136:
    case 137: case 138: case 139: case 140: case 142: case 145: case 146: case 147:
    case 150: case 151: case 152: case 157: case 158: case 159: case 160: case 161:
        return 0;
    case 119: case 128: case 141: case 143: case 144: case 148: case 149: case 153:
    case 154: case 155: case 162: case 163:
        return 1;
    default:
        return -1;
    }
}

int m3_fish_frame(int source_sprite)
{
    switch(source_sprite)
    {
    case 110: return 3; case 111: return 1; case 119: return 11; case 120: return 29;
    case 121: return 16; case 122: return 17; case 123: return 6; case 126: return 7;
    case 127: return 18; case 128: return 7; case 129: return 8; case 130: return 9;
    case 131: return 0; case 132: return 2; case 133: return 14; case 134: return 4;
    case 135: return 19; case 136: return 10; case 137: return 11; case 138: return 5;
    case 139: return 30; case 140: return 20; case 141: return 8; case 142: return 21;
    case 143: return 4; case 144: return 5; case 145: return 22; case 146: return 15;
    case 147: return 31; case 148: return 0; case 149: return 9; case 150: return 23;
    case 151: return 24; case 152: return 12; case 153: return 2; case 154: return 10;
    case 155: return 1; case 157: return 25; case 158: return 26; case 159: return 27;
    case 160: return 28; case 161: return 13; case 162: return 3; case 163: return 6;
    default: return -1;
    }
}

bn::sprite_ptr create_fish_sprite(int source_sprite, int x, int y)
{
    const int frame = m3_fish_frame(source_sprite);
    if(m3_fish_bank(source_sprite) == 1)
    {
        return bn::sprite_items::fishing_fish_m3_1.create_sprite(x, y, frame);
    }
    return bn::sprite_items::fishing_fish_m3_0.create_sprite(x, y, frame);
}

template<int MaxSprites>
void append_text(bn::vector<bn::sprite_ptr, MaxSprites>& sprites, const char* text, int screen_x, int screen_y,
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

CatalogScene::CatalogScene() :
    _background(bn::regular_bg_items::m4_catalog_anim.create_bg(0, 0, 0)),
    _cursor(bn::sprite_items::m4_catalog_cursor.create_sprite(-91, -46, 0))
{
}

void CatalogScene::update(FlowModel& flow)
{
    if(! _grid_built)
    {
        _build_fish_grid(flow);
        _grid_built = true;
    }

    if(bn::keypad::b_pressed())
    {
        _audio_event = AudioCue::NextPage;
        if(_dialog.active())
        {
            _dialog.clear();
            _dialog_renderer.hide();
        }
        else
        {
            flow.handle_catalog_back(_model.complete(flow));
            return;
        }
    }
    else if(_dialog.active())
    {
        const DialogEvent event = _dialog.update(bn::keypad::a_pressed());
        if(event == DialogEvent::NextPage)
        {
            _audio_event = AudioCue::NextPage;
        }
    }
    else if(bn::keypad::left_pressed())
    {
        _audio_event = AudioCue::NextPage;
        _model.move_left();
    }
    else if(bn::keypad::right_pressed())
    {
        _audio_event = AudioCue::NextPage;
        _model.move_right();
    }
    else if(bn::keypad::up_pressed())
    {
        _audio_event = AudioCue::NextPage;
        _model.move_up();
    }
    else if(bn::keypad::down_pressed())
    {
        _audio_event = AudioCue::NextPage;
        _model.move_down();
    }
    else if(bn::keypad::a_pressed() && _model.selected_caught(flow))
    {
        if(const CatalogEntrySpec* entry = _model.selected_entry())
        {
            _dialog.start(entry->description);
            _audio_event = AudioCue::NextPage;
        }
    }

    _advance_background();
    _update_cursor();
    _render_text(flow);
    if(_dialog.active())
    {
        _dialog_renderer.render(_dialog);
    }
    else
    {
        _dialog_renderer.hide();
    }
}

void CatalogScene::_advance_background()
{
    ++_sea_ticks;
    int next_map = _map_index;
    if(_sea_ticks == 1) next_map = 1;
    else if(_sea_ticks == 13) next_map = 2;
    else if(_sea_ticks == 25) next_map = 1;
    else if(_sea_ticks == 37) next_map = 0;
    else if(_sea_ticks == 49) _sea_ticks = 0;
    if(next_map != _map_index)
    {
        _map_index = next_map;
        _background.set_map(bn::regular_bg_items::m4_catalog_anim.map_item(), _map_index);
    }
}

void CatalogScene::_build_fish_grid(const FlowModel& flow)
{
    for(int cursor = 0; cursor < catalog_entry_count(); ++cursor)
    {
        const CatalogEntrySpec* entry = catalog_entry_spec(cursor);
        if(! entry)
        {
            continue;
        }
        const int source_sprite = fish_source_sprite(entry->fish_number);
        const int column = cursor % 11;
        const int row = cursor / 11;
        bn::sprite_ptr fish = create_fish_sprite(
            source_sprite, 29 + column * 18 - 120, 39 + row * 22 - 80);
        fish.set_visible(flow.catalog_has_fish(entry->fish_number));
        _fish_sprites.push_back(bn::move(fish));
    }
}

void CatalogScene::_render_text(const FlowModel& flow)
{
    _text_sprites.clear();
    const CatalogEntrySpec* entry = _model.selected_entry();
    if(! entry)
    {
        return;
    }

    if(_model.selected_caught(flow))
    {
        append_text(_text_sprites, entry->name, 126, 8, 11);
    }
    else
    {
        append_text(_text_sprites, "???", 126, 8, 3);
    }
}

void CatalogScene::_update_cursor()
{
    const int cursor = _model.selected_cursor();
    const int column = cursor % 11;
    const int row = cursor / 11;
    _cursor.set_position(29 + column * 18 - 120, 39 + row * 22 - 80);
}



AudioCue CatalogScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
