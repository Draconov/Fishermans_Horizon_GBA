#include "shop_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_m4_shop.h"
#include "bn_sprite_items_m4_font.h"
#include "bn_sprite_items_m4_shop_cursor.h"
#include "bn_sprite_items_m4_shop_keeper.h"
#include "bn_sprite_items_m4_shop_sold_out.h"

#include "shop_model.h"
#include "flow_model.h"
#include "m4_font.h"

namespace fh
{
namespace
{

void append_text(bn::vector<bn::sprite_ptr, 64>& sprites, const char* text, int screen_x, int screen_y,
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

void append_number(bn::vector<bn::sprite_ptr, 64>& sprites, int value, int screen_x, int screen_y)
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

void append_money(bn::vector<bn::sprite_ptr, 64>& sprites, int value, int screen_x, int screen_y)
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

ShopScene::ShopScene() :
    _background(bn::regular_bg_items::m4_shop.create_bg(0, 0)),
    _keeper(bn::sprite_items::m4_shop_keeper.create_sprite(-84, 21, 0)),
    _cursor(bn::sprite_items::m4_shop_cursor.create_sprite(12, -44, 0))
{
    for(int slot = 0; slot < 16; ++slot)
    {
        const int column = slot % 4;
        const int row = slot / 4;
        bn::sprite_ptr sold_out = bn::sprite_items::m4_shop_sold_out.create_sprite(
            12 + column * 24, -44 + row * 24, 0);
        sold_out.set_visible(false);
        _sold_out_sprites.push_back(bn::move(sold_out));
    }
}

void ShopScene::update(FlowModel& flow)
{
    if(bn::keypad::b_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_shop_back();
        return;
    }

    if(bn::keypad::left_pressed() || bn::keypad::up_pressed())
    {
        _audio_event = AudioCue::NextPage;
        _model.previous();
        _last_result = ShopPurchaseResult::InvalidItem;
        _dirty = true;
    }
    else if(bn::keypad::right_pressed() || bn::keypad::down_pressed())
    {
        _audio_event = AudioCue::NextPage;
        _model.next();
        _last_result = ShopPurchaseResult::InvalidItem;
        _dirty = true;
    }
    else if(bn::keypad::a_pressed())
    {
        _last_result = _model.purchase(flow);
        _audio_event = _last_result == ShopPurchaseResult::Purchased ? AudioCue::Coin : AudioCue::NextPage;
        _dirty = true;
    }

    ++_keeper_ticks;
    if(_keeper_ticks >= 20)
    {
        _keeper_ticks = 0;
        _keeper_frame = 1 - _keeper_frame;
        _keeper.set_tiles(bn::sprite_items::m4_shop_keeper.tiles_item(), _keeper_frame);
    }

    const int slot = _model.selected_item();
    _cursor.set_position(12 + (slot % 4) * 24, -44 + (slot / 4) * 24);
    _render(flow);
}

void ShopScene::_render(FlowModel& flow)
{
    for(int slot = 0; slot < int(_sold_out_sprites.size()); ++slot)
    {
        _sold_out_sprites[slot].set_visible(flow.shop_item_owned(slot));
    }

    if(! _dirty)
    {
        return;
    }
    _dirty = false;
    _text_sprites.clear();

    const ShopItemSpec* item = shop_item_spec(_model.selected_item());
    if(item)
    {
        append_text(_text_sprites, item->name, 126, 8, 11);
        append_number(_text_sprites, item->price, 24, 144);
    }
    append_money(_text_sprites, flow.money(), 193, 144);
}



AudioCue ShopScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
