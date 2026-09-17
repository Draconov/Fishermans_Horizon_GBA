#include "options_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_options_bg.h"
#include "bn_sprite_items_ui_font.h"

#include "options_model.h"
#include "flow_model.h"
#include "ui_font.h"
#include "ui_text_layout.h"

namespace fh
{
namespace
{

void append_text(bn::vector<bn::sprite_ptr, 32>& sprites, const char* text, int screen_x, int screen_y,
                 int max_chars)
{
    int pen_x = 0;
    int count = 0;
    while(*text && count < max_chars && sprites.size() < sprites.max_size())
    {
        const char character = *text++;
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

OptionsScene::OptionsScene() :
    _background(bn::regular_bg_items::options_bg.create_bg(0, 0, 0))
{
}

void OptionsScene::update(FlowModel& flow)
{
    if(bn::keypad::b_pressed())
    {
        _audio_event = AudioCue::NextPage;
        _model.back(flow);
        return;
    }
    if(bn::keypad::a_pressed() || bn::keypad::left_pressed() || bn::keypad::right_pressed())
    {
        _audio_event = AudioCue::NextPage;
        _model.toggle_sound(flow);
    }

    _advance_background();
    _render(flow);
}

void OptionsScene::_advance_background()
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
        _background.set_map(bn::regular_bg_items::options_bg.map_item(), _map_index);
    }
}

void OptionsScene::_render(const FlowModel& flow)
{
    _text_sprites.clear();
    append_text(_text_sprites, _model.sound(flow) ? "on" : "off", 170, 8, 3);
}



AudioCue OptionsScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
