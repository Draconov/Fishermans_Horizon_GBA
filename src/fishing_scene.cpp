#include "fishing_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_fishing_area_cave.h"
#include "bn_regular_bg_items_fishing_area_crystal.h"
#include "bn_regular_bg_items_fishing_area_ocean.h"
#include "bn_regular_bg_items_fishing_area_pier.h"
#include "bn_regular_bg_items_fishing_area_river.h"
#include "bn_sprite_items_fishing_bait.h"
#include "bn_sprite_items_fishing_char.h"
#include "bn_sprite_items_fishing_char_m4_0.h"
#include "bn_sprite_items_fishing_char_m4_1.h"
#include "bn_sprite_items_fishing_char_m4_2.h"
#include "bn_sprite_items_fishing_char_m4_3.h"
#include "bn_sprite_items_fishing_char_m4_4.h"
#include "bn_sprite_items_fishing_char_m4_5.h"
#include "bn_sprite_items_fishing_coin.h"
#include "bn_sprite_items_fishing_fish_m3_0.h"
#include "bn_sprite_items_fishing_fish_m3_1.h"
#include "bn_sprite_items_fishing_hud.h"
#include "bn_sprite_items_fishing_line_dot.h"
#include "bn_sprite_items_fishing_meter.h"
#include "bn_sprite_items_m4_font.h"
#include "bn_sprite_items_fishing_rods_left.h"
#include "bn_sprite_items_fishing_rods_right.h"
#include "bn_sprite_items_fishing_splash.h"

#include "audio_policy.h"
#include "flow_model.h"
#include "m4_font.h"

namespace fh
{
namespace
{

bn::regular_bg_ptr create_fishing_background(int pool)
{
    switch(pool)
    {
    case 2: return bn::regular_bg_items::fishing_area_pier.create_bg(0, 0, 0);
    case 3: return bn::regular_bg_items::fishing_area_river.create_bg(0, 0, 0);
    case 4: return bn::regular_bg_items::fishing_area_ocean.create_bg(0, 0, 0);
    case 5: return bn::regular_bg_items::fishing_area_cave.create_bg(0, 0, 0);
    default: return bn::regular_bg_items::fishing_area_crystal.create_bg(0, 0, 0);
    }
}

void set_fishing_background_map(bn::regular_bg_ptr& background, int pool, int map_index)
{
    switch(pool)
    {
    case 2:
        background.set_map(bn::regular_bg_items::fishing_area_pier.map_item(), map_index);
        break;
    case 3:
        background.set_map(bn::regular_bg_items::fishing_area_river.map_item(), map_index);
        break;
    case 4:
        background.set_map(bn::regular_bg_items::fishing_area_ocean.map_item(), map_index);
        break;
    case 5:
        background.set_map(bn::regular_bg_items::fishing_area_cave.map_item(), map_index);
        break;
    default:
        background.set_map(bn::regular_bg_items::fishing_area_crystal.map_item(), map_index);
        break;
    }
}

int m3_fish_bank(int source_sprite)
{
    switch(source_sprite)
    {
    case 110: return 0;
    case 111: return 0;
    case 119: return 1;
    case 120: return 0;
    case 121: return 0;
    case 122: return 0;
    case 123: return 0;
    case 126: return 0;
    case 127: return 0;
    case 128: return 1;
    case 129: return 0;
    case 130: return 0;
    case 131: return 0;
    case 132: return 0;
    case 133: return 0;
    case 134: return 0;
    case 135: return 0;
    case 136: return 0;
    case 137: return 0;
    case 138: return 0;
    case 139: return 0;
    case 140: return 0;
    case 141: return 1;
    case 142: return 0;
    case 143: return 1;
    case 144: return 1;
    case 145: return 0;
    case 146: return 0;
    case 147: return 0;
    case 148: return 1;
    case 149: return 1;
    case 150: return 0;
    case 151: return 0;
    case 152: return 0;
    case 153: return 1;
    case 154: return 1;
    case 155: return 1;
    case 157: return 0;
    case 158: return 0;
    case 159: return 0;
    case 160: return 0;
    case 161: return 0;
    case 162: return 1;
    case 163: return 1;
    default: return -1;
    }
}

int m3_fish_frame(int source_sprite)
{
    switch(source_sprite)
    {
    case 110: return 3;
    case 111: return 1;
    case 119: return 11;
    case 120: return 29;
    case 121: return 16;
    case 122: return 17;
    case 123: return 6;
    case 126: return 7;
    case 127: return 18;
    case 128: return 7;
    case 129: return 8;
    case 130: return 9;
    case 131: return 0;
    case 132: return 2;
    case 133: return 14;
    case 134: return 4;
    case 135: return 19;
    case 136: return 10;
    case 137: return 11;
    case 138: return 5;
    case 139: return 30;
    case 140: return 20;
    case 141: return 8;
    case 142: return 21;
    case 143: return 4;
    case 144: return 5;
    case 145: return 22;
    case 146: return 15;
    case 147: return 31;
    case 148: return 0;
    case 149: return 9;
    case 150: return 23;
    case 151: return 24;
    case 152: return 12;
    case 153: return 2;
    case 154: return 10;
    case 155: return 1;
    case 157: return 25;
    case 158: return 26;
    case 159: return 27;
    case 160: return 28;
    case 161: return 13;
    case 162: return 3;
    case 163: return 6;
    default: return -1;
    }
}

int bait_frame(int source_sprite)
{
    switch(source_sprite)
    {
    case 11: return 0;
    case 12: return 1;
    case 75: return 2;
    case 76: return 3;
    case 13: return 4;
    case 14: return 5;
    case 77: return 6;
    case 78: return 7;
    case 88: return 8;
    case 89: return 9;
    case 90: return 10;
    case 91: return 11;
    case 92: return 12;
    case 93: return 13;
    case 124: return 14;
    default: return -1;
    }
}

bn::sprite_ptr create_character_sprite(int character_index)
{
    switch(character_index)
    {
    case 1: return bn::sprite_items::fishing_char_m4_1.create_sprite(-88, 24, 0);
    case 2: return bn::sprite_items::fishing_char_m4_2.create_sprite(-88, 24, 0);
    case 3: return bn::sprite_items::fishing_char_m4_3.create_sprite(-88, 24, 0);
    case 4: return bn::sprite_items::fishing_char_m4_4.create_sprite(-88, 24, 0);
    case 5: return bn::sprite_items::fishing_char_m4_5.create_sprite(-88, 24, 0);
    default: return bn::sprite_items::fishing_char_m4_0.create_sprite(-88, 24, 0);
    }
}

void set_character_frame(bn::sprite_ptr& sprite, int character_index, int frame)
{
    switch(character_index)
    {
    case 1: sprite.set_tiles(bn::sprite_items::fishing_char_m4_1.tiles_item(), frame); break;
    case 2: sprite.set_tiles(bn::sprite_items::fishing_char_m4_2.tiles_item(), frame); break;
    case 3: sprite.set_tiles(bn::sprite_items::fishing_char_m4_3.tiles_item(), frame); break;
    case 4: sprite.set_tiles(bn::sprite_items::fishing_char_m4_4.tiles_item(), frame); break;
    case 5: sprite.set_tiles(bn::sprite_items::fishing_char_m4_5.tiles_item(), frame); break;
    default: sprite.set_tiles(bn::sprite_items::fishing_char_m4_0.tiles_item(), frame); break;
    }
}

void append_dialog_text(char* output, int& length, int capacity, const char* text)
{
    while(text && *text && length + 1 < capacity)
    {
        output[length++] = *text++;
    }
    output[length] = '\0';
}

void append_dialog_number(char* output, int& length, int capacity, int value)
{
    if(value < 0)
    {
        if(length + 1 < capacity)
        {
            output[length++] = '-';
        }
        value = -value;
    }

    char digits[12];
    int count = 0;
    do
    {
        digits[count++] = char('0' + value % 10);
        value /= 10;
    }
    while(value && count < int(sizeof(digits)));

    while(count > 0 && length + 1 < capacity)
    {
        output[length++] = digits[--count];
    }
    output[length] = '\0';
}

const char* bait_name_for_index(int equipped_bait)
{
    constexpr const char* NAMES[] = {
        "Worm", "Bread", "Candy", "Bitter Gum", "Steak", "Rainboworm", "Bait X",
    };
    if(equipped_bait < 0 || equipped_bait >= 7)
    {
        return NAMES[0];
    }
    return NAMES[equipped_bait];
}

void append_text(bn::vector<bn::sprite_ptr, 16>& sprites, const char* text, int screen_x, int screen_y,
                 int max_chars)
{
    int column = 0;
    while(*text && column < max_chars && sprites.size() < sprites.max_size())
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
                screen_x + column * 8 + 4 - 120, screen_y + 4 - 80, glyph));
        }
        ++column;
    }
}

void append_money(bn::vector<bn::sprite_ptr, 16>& sprites, int value, int screen_x, int screen_y)
{
    const char text[4] = {
        char('0' + (value / 100) % 10),
        char('0' + (value / 10) % 10),
        char('0' + value % 10),
        0,
    };
    append_text(sprites, text, screen_x, screen_y, 3);
}

int absolute(int value)
{
    return value < 0 ? -value : value;
}

}

FishingScene::FishingScene(int pool, int rod_index, int equipped_bait, int character_index) :
    _pool(pool),
    _character_index(character_index),
    _model(pool, rod_index, equipped_bait),
    _background(create_fishing_background(pool)),
    _character(create_character_sprite(character_index)),
    _rod_left(bn::sprite_items::fishing_rods_left.create_sprite(-88, 0, rod_index * 12)),
    _rod_right_top(bn::sprite_items::fishing_rods_right.create_sprite(-48, -16, rod_index * 24)),
    _rod_right_bottom(bn::sprite_items::fishing_rods_right.create_sprite(-48, 16, rod_index * 24 + 1)),
    _bait(bn::sprite_items::fishing_bait.create_sprite(-64, 8, 0)),
    _fish_bank0(bn::sprite_items::fishing_fish_m3_0.create_sprite(-64, 8, 0)),
    _fish_bank1(bn::sprite_items::fishing_fish_m3_1.create_sprite(-64, 8, 0)),
    _splash(bn::sprite_items::fishing_splash.create_sprite(-64, 44, 0)),
    _coin(bn::sprite_items::fishing_coin.create_sprite(-68, 0, 0)),
    _back_icon(bn::sprite_items::fishing_hud.create_sprite(-108, -68, 0)),
    _bait_icon(bn::sprite_items::fishing_hud.create_sprite(108, -68, 1)),
    _meter(bn::sprite_items::fishing_meter.create_sprite(-79, 69, 0))
{
    _fish_bank0.set_visible(false);
    _fish_bank1.set_visible(false);
    _splash.set_visible(false);
    _coin.set_visible(false);

    for(int index = 0; index < 32; ++index)
    {
        bn::sprite_ptr dot = bn::sprite_items::fishing_line_dot.create_sprite(0, 0, 0);
        dot.set_visible(false);
        _line_dots.push_back(bn::move(dot));
    }

    _render();
}

void FishingScene::update(FlowModel& flow)
{
    DialogEvent dialog_event = DialogEvent::None;
    if(_dialog.active())
    {
        dialog_event = _dialog.update(bn::keypad::a_pressed());
    }

    if(bn::keypad::select_pressed() && _model.state() == FishingState::Stand && ! _model.dialog_alive() &&
       ! _dialog.active())
    {
        _model.set_equipped_bait(flow.cycle_owned_bait());
    }

    FishingInput input;
    input.rod_held = bn::keypad::a_held() && ! _model.dialog_alive() && ! _dialog.active();
    input.confirm_dialog = false;
    if(dialog_event == DialogEvent::Closed && _model.dialog_alive())
    {
        input.confirm_dialog = true;
    }
    input.back = bn::keypad::b_pressed() && ! _model.dialog_alive() && ! _dialog.active();

    const int random_roll = _model.needs_random_roll() ? _random.get_int(10) : 0;
    _model.update(input, random_roll);

    const AudioCue fishing_audio = audio_cue_from_fishing(_model.take_sound_event());
    if(dialog_event == DialogEvent::NextPage)
    {
        _audio_event = AudioCue::NextPage;
    }
    else if(fishing_audio != AudioCue::None)
    {
        _audio_event = fishing_audio;
    }

    if(_model.state() == FishingState::LineBreak && _model.ticks() == 1)
    {
        _flash_request = true;
    }

    if(_model.dialog_alive() && ! _dialog.active())
    {
        _start_result_dialog();
    }

    const FishingReward reward = _model.take_reward();
    if(reward.valid)
    {
        flow.apply_fishing_reward(reward.fish_number, reward.amount);
    }

    if(_model.exit_requested())
    {
        _model.clear_exit_request();
        flow.handle_fishing_back();
        return;
    }

    _render();
    _render_hud_text(flow);
    if(_dialog.active())
    {
        _dialog_renderer.render(_dialog);
    }
    else
    {
        _dialog_renderer.hide();
    }
}

void FishingScene::_start_result_dialog()
{
    int length = 0;
    _dialog_text[0] = '\0';
    if(_model.dialog_kind() == FishingDialog::Catch)
    {
        append_dialog_text(_dialog_text, length, int(sizeof(_dialog_text)), _model.dialog_fish_name());
        append_dialog_text(_dialog_text, length, int(sizeof(_dialog_text)), " was caught!#You got ");
        append_dialog_number(_dialog_text, length, int(sizeof(_dialog_text)), _model.current_reward());
        append_dialog_text(_dialog_text, length, int(sizeof(_dialog_text)), "$!");
    }
    else
    {
        append_dialog_text(_dialog_text, length, int(sizeof(_dialog_text)), "The line broke...");
    }
    _dialog.start(_dialog_text);
}

void FishingScene::_render()
{
    const int map_index = _model.sea_tile() - 112;
    if(map_index != _background_map_index)
    {
        set_fishing_background_map(_background, _pool, map_index);
        _background_map_index = map_index;
    }

    set_character_frame(_character, _character_index, _model.char_frame());
    const int rod_frame = _model.rod_index() * 12 + _model.stick_frame();
    _rod_left.set_tiles(bn::sprite_items::fishing_rods_left.tiles_item(), rod_frame);
    _rod_right_top.set_tiles(bn::sprite_items::fishing_rods_right.tiles_item(), rod_frame * 2);
    _rod_right_bottom.set_tiles(bn::sprite_items::fishing_rods_right.tiles_item(), rod_frame * 2 + 1);

    _meter.set_position(_model.meter_x() - 116, 69);

    _splash.set_visible(_model.draw_splash());
    if(_model.draw_splash())
    {
        _splash.set_tiles(bn::sprite_items::fishing_splash.tiles_item(), _model.splash_frame() - 104);
        _splash.set_position(int(_model.line_distance()) - 112, 44);
    }

    _coin.set_visible(_model.draw_coin());
    if(_model.draw_coin())
    {
        _coin.set_tiles(bn::sprite_items::fishing_coin.tiles_item(), _model.coin_frame() - 116);
        _coin.set_position(-68, _model.coin_y() - 76);
    }

    _render_bait_or_fish();
    _render_line();

    const bool hud_visible = ! _model.dialog_alive() || ((_model.ticks() / 8) % 2 == 0);
    _back_icon.set_visible(hud_visible);
    _bait_icon.set_visible(hud_visible);
}

void FishingScene::_render_hud_text(const FlowModel& flow)
{
    const int equipped_bait = _model.equipped_bait();
    const int money = flow.money();
    const bool dialog_active = _dialog.active();
    if(equipped_bait == _last_hud_bait && money == _last_hud_money &&
       dialog_active == _last_hud_dialog_active)
    {
        return;
    }

    _last_hud_bait = equipped_bait;
    _last_hud_money = money;
    _last_hud_dialog_active = dialog_active;
    _hud_text_sprites.clear();

    const char* bait_name = bait_name_for_index(equipped_bait);
    append_text(_hud_text_sprites, bait_name, 126, 8, 11);
    // The result dialog covers the bottom HUD, so release its three money
    // glyphs while the dialog is active to preserve GBA OAM headroom.
    if(! dialog_active)
    {
        append_money(_hud_text_sprites, flow.money(), 193, 144);
    }
}

void FishingScene::_render_bait_or_fish()
{
    _bait.set_visible(false);
    _fish_bank0.set_visible(false);
    _fish_bank1.set_visible(false);

    if(! _model.draw_bait())
    {
        return;
    }

    const int source_sprite = _model.bait_sprite();
    const int x = _model.bait_x() - 112;
    const int y = _model.bait_y() - 64;

    const int bait_index = bait_frame(source_sprite);
    if(bait_index >= 0)
    {
        _bait.set_tiles(bn::sprite_items::fishing_bait.tiles_item(), bait_index);
        _bait.set_position(x, y);
        _bait.set_visible(true);
        return;
    }

    const int bank = m3_fish_bank(source_sprite);
    const int frame = m3_fish_frame(source_sprite);
    if(bank == 0 && frame >= 0)
    {
        _fish_bank0.set_tiles(bn::sprite_items::fishing_fish_m3_0.tiles_item(), frame);
        _fish_bank0.set_position(x, y);
        _fish_bank0.set_visible(true);
    }
    else if(bank == 1 && frame >= 0)
    {
        _fish_bank1.set_tiles(bn::sprite_items::fishing_fish_m3_1.tiles_item(), frame);
        _fish_bank1.set_position(x, y);
        _fish_bank1.set_visible(true);
    }
}

void FishingScene::_render_line()
{
    for(bn::sprite_ptr& dot : _line_dots)
    {
        dot.set_visible(false);
    }

    if(! _model.draw_line())
    {
        return;
    }

    const int x1 = _model.line_x1();
    const int y1 = _model.line_y1();
    const int x2 = int(_model.line_distance());
    const int y2 = _model.line_y2();
    const int dx = x2 - x1;
    const int dy = y2 - y1;
    int extent = absolute(dx);
    if(absolute(dy) > extent)
    {
        extent = absolute(dy);
    }

    int point_count = extent / 6 + 1;
    if(point_count < 2)
    {
        point_count = 2;
    }
    if(point_count > 32)
    {
        point_count = 32;
    }

    const int denominator = point_count - 1;
    for(int index = 0; index < point_count; ++index)
    {
        const int x = x1 + (dx * index) / denominator;
        const int y = y1 + (dy * index) / denominator;
        bn::sprite_ptr& dot = _line_dots[index];
        dot.set_position(x - 120, y - 80);
        dot.set_visible(true);
    }
}



AudioCue FishingScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

bool FishingScene::take_flash_request() noexcept
{
    const bool result = _flash_request;
    _flash_request = false;
    return result;
}

}
