#include "shop_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_shop_bg.h"
#include "bn_regular_bg_items_shop_bg_region2.h"
#include "bn_sprite_items_ui_font.h"
#include "bn_sprite_items_shop_buy_enabled.h"
#include "bn_sprite_items_shop_cursor.h"
#include "bn_sprite_items_shop_keeper.h"
#include "bn_sprite_items_shop_locked.h"
#include "bn_sprite_items_shop_sold_out.h"

#include "flow_model.h"
#include "ui_font.h"
#include "ui_text_layout.h"
#include "shop_model.h"

namespace fh
{
namespace
{

constexpr const char* SHOP_WELCOME_TEXT = "Welcome to Mari-Mari Shop";
constexpr const char* SHOP2_WELCOME_TEXT = "Welcome to Jarim Perla Shop";

bn::regular_bg_ptr create_shop_background(ShopId shop)
{
    if(shop == ShopId::JarimPerla)
    {
        return bn::regular_bg_items::shop_bg_region2.create_bg(0, 0);
    }
    return bn::regular_bg_items::shop_bg.create_bg(0, 0);
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

template<int MaxSprites>
void append_number(bn::vector<bn::sprite_ptr, MaxSprites>& sprites, int value, int screen_x, int screen_y)
{
    char text[4] = {'0', 0, 0, 0};
    if(value >= 100)
    {
        text[0] = char('0' + (value / 100) % 10);
        text[1] = char('0' + (value / 10) % 10);
        text[2] = char('0' + value % 10);
    }
    else if(value >= 10)
    {
        text[0] = char('0' + value / 10);
        text[1] = char('0' + value % 10);
    }
    else
    {
        text[0] = char('0' + value);
    }
    append_text(sprites, text, screen_x, screen_y, 3);
}

template<int MaxSprites>
void append_money(bn::vector<bn::sprite_ptr, MaxSprites>& sprites, int value, int screen_x, int screen_y)
{
    const char text[4] = {
        char('0' + (value / 100) % 10),
        char('0' + (value / 10) % 10),
        char('0' + value % 10),
        0,
    };
    append_text(sprites, text, screen_x, screen_y, 3);
}

}

ShopScene::ShopScene(ShopId shop) :
    _shop_id(shop),
    _model(shop),
    _background(create_shop_background(shop)),
    _keeper(bn::sprite_items::shop_keeper.create_sprite(-64, 16, 0)),
    _cursor(bn::sprite_items::shop_cursor.create_sprite(16, -40, 0)),
    _locked_overlay(bn::sprite_items::shop_locked.create_sprite(88, -16, 0)),
    _buy_enabled(bn::sprite_items::shop_buy_enabled.create_sprite(-108, 68, 0))
{
    // Lower z-order is drawn later/on top in Butano. The locked Nova overlay
    // is opaque, so keep it behind the selection cursor.
    _locked_overlay.set_z_order(1);
    _cursor.set_z_order(0);
    _locked_overlay.set_visible(false);
    _buy_enabled.set_visible(false);
    _cursor.set_visible(false);
    _dialog.start(_shop_id == ShopId::JarimPerla ? SHOP2_WELCOME_TEXT : SHOP_WELCOME_TEXT);

    for(int slot = 0; slot < 16; ++slot)
    {
        const int column = slot % 4;
        const int row = slot / 4;
        bn::sprite_ptr sold_out = bn::sprite_items::shop_sold_out.create_sprite(
            12 + column * 24, -44 + row * 24, 0);
        sold_out.set_visible(false);
        _sold_out_sprites.push_back(bn::move(sold_out));
    }
}

void ShopScene::update(FlowModel& flow)
{
    ++_shop_ticks;

    if(_welcome_active)
    {
        const DialogEvent event = _dialog.update(bn::keypad::a_pressed());
        if(event == DialogEvent::NextPage)
        {
            _audio_event = AudioCue::NextPage;
        }
        if(event == DialogEvent::Closed)
        {
            _welcome_active = false;
            _dirty = true;
        }
    }
    else if(_dialog.active())
    {
        if(bn::keypad::b_pressed())
        {
            _audio_event = AudioCue::NextPage;
            _dialog.clear();
            _dialog_renderer.hide();
            _dirty = true;
        }
        else
        {
            const DialogEvent event = _dialog.update(bn::keypad::a_pressed());
            if(event == DialogEvent::NextPage)
            {
                _audio_event = AudioCue::NextPage;
            }
            if(event == DialogEvent::Closed)
            {
                _dirty = true;
            }
        }
    }
    else
    {
        const int previous_page = _model.page();
        bool moved = false;
        if(bn::keypad::left_pressed())
        {
            (void) _model.push_cheat_key(ShopCheatKey::Left, _shop_ticks);
            _model.move_left();
            moved = true;
        }
        else if(bn::keypad::right_pressed())
        {
            (void) _model.push_cheat_key(ShopCheatKey::Right, _shop_ticks);
            _model.move_right();
            moved = true;
        }
        else if(bn::keypad::up_pressed())
        {
            (void) _model.push_cheat_key(ShopCheatKey::Up, _shop_ticks);
            _model.move_up();
            moved = true;
        }
        else if(bn::keypad::down_pressed())
        {
            (void) _model.push_cheat_key(ShopCheatKey::Down, _shop_ticks);
            _model.move_down();
            moved = true;
        }

        if(moved)
        {
            if(_model.page() != previous_page)
            {
                _set_background_page(_model.page());
            }
            _audio_event = AudioCue::NextPage;
            _last_result = ShopPurchaseResult::InvalidItem;
            _dirty = true;
        }
        else if(bn::keypad::select_pressed())
        {
            _model.reset_cheat();
            _start_description(flow);
            if(_dialog.active())
            {
                _audio_event = AudioCue::NextPage;
                _dirty = true;
            }
        }
        else if(bn::keypad::b_pressed())
        {
            const ShopCheatResult cheat = _model.push_cheat_key(ShopCheatKey::B, _shop_ticks);
            if(cheat != ShopCheatResult::Progressed)
            {
                flow.handle_shop_back();
                return;
            }
        }
        else if(bn::keypad::a_pressed())
        {
            const ShopCheatResult cheat = _model.push_cheat_key(ShopCheatKey::A, _shop_ticks);
            if(cheat == ShopCheatResult::Completed)
            {
                flow.grant_money(30);
                _audio_event = AudioCue::Coin;
                _dirty = true;
            }
            else
            {
                _last_result = _model.purchase(flow);
                _audio_event = _last_result == ShopPurchaseResult::Purchased ? AudioCue::Coin : AudioCue::NextPage;
                _dirty = true;
            }
        }
        else if(bn::keypad::l_pressed())
        {
            _model.reset_cheat();
            _model.previous_page();
            _set_background_page(_model.page());
            _last_result = ShopPurchaseResult::InvalidItem;
            _audio_event = AudioCue::NextPage;
            _dirty = true;
        }
        else if(bn::keypad::r_pressed())
        {
            _model.reset_cheat();
            _model.next_page();
            _set_background_page(_model.page());
            _last_result = ShopPurchaseResult::InvalidItem;
            _audio_event = AudioCue::NextPage;
            _dirty = true;
        }
    }

    _update_keeper_animation();

    const int slot = _model.selected_item() % 16;
    _cursor.set_position(16 + (slot % 4) * 24, -40 + (slot / 4) * 24);
    _cursor.set_visible(! _welcome_active);
    _render(flow);

    if(_dialog.active())
    {
        _dialog_renderer.render(_dialog);
    }
    else
    {
        _dialog_renderer.hide();
    }
}

void ShopScene::_start_description(const FlowModel& flow)
{
    if(flow.shop_item_locked(_shop_id, _model.selected_item()))
    {
        _dialog.clear();
        return;
    }

    if(const ShopItemSpec* item = shop_item_spec(_shop_id, _model.selected_item()))
    {
        _dialog.start(item->description);
    }
}

void ShopScene::_update_keeper_animation()
{
    if(_dialog.talking())
    {
        ++_keeper_ticks;
        if(_keeper_ticks % 8 == 0)
        {
            _set_keeper_frame(0);
            _keeper_ticks = 0;
        }
        else if(_keeper_ticks % 4 == 0)
        {
            _set_keeper_frame(1);
        }
    }
    else if(_keeper_ticks > 0)
    {
        ++_keeper_ticks;
        if(_keeper_ticks % 12 == 0)
        {
            _set_keeper_frame(0);
            _keeper_ticks = 0;
        }
    }
}

void ShopScene::_set_keeper_frame(int frame)
{
    if(frame != _keeper_frame)
    {
        _keeper_frame = frame;
        _keeper.set_tiles(bn::sprite_items::shop_keeper.tiles_item(), frame);
    }
}

void ShopScene::_render(FlowModel& flow)
{
    const int page_start = _model.page() * 16;
    for(int local_slot = 0; local_slot < int(_sold_out_sprites.size()); ++local_slot)
    {
        const int item_slot = page_start + local_slot;
        _sold_out_sprites[local_slot].set_visible(
            item_slot < shop_item_count(_shop_id) && flow.shop_item_owned(_shop_id, item_slot));
    }

    _locked_overlay.set_visible(_shop_id == ShopId::MariMari && _model.page() == 0 && flow.shop_item_locked(_shop_id, 7));
    _buy_enabled.set_visible(! _dialog.active() && flow.shop_item_purchasable(_shop_id, _model.selected_item()));

    if(_dialog.active())
    {
        _text_sprites.clear();
        _dirty = true;
        return;
    }

    if(! _dirty)
    {
        return;
    }
    _dirty = false;
    _text_sprites.clear();

    const int slot = _model.selected_item();
    const ShopItemSpec* item = shop_item_spec(_shop_id, slot);
    if(item)
    {
        if(flow.shop_item_locked(_shop_id, slot))
        {
            append_text(_text_sprites, "???", 126, 8, 11);
            append_text(_text_sprites, "-", 24, 144, 3);
        }
        else
        {
            if(slot >= 16)
            {
                append_text(_text_sprites, item->name, 126, 8, 14);
            }
            else
            {
                append_text(_text_sprites, item->name, 126, 8, 11);
            }
            if(flow.shop_item_owned(_shop_id, slot))
            {
                append_text(_text_sprites, "-", 24, 144, 3);
            }
            else
            {
                append_number(_text_sprites, item->price, 24, 144);
            }
        }
    }
    append_money(_text_sprites, flow.money(), 193, 144);
}

void ShopScene::_set_background_page(int page)
{
    if(_shop_id == ShopId::JarimPerla)
    {
        _background.set_map(bn::regular_bg_items::shop_bg_region2.map_item(), page);
    }
    else
    {
        _background.set_map(bn::regular_bg_items::shop_bg.map_item(), page);
    }
}

AudioCue ShopScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
