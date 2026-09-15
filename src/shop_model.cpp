#include "shop_model.h"

#include "flow_model.h"

#include <array>

namespace fh
{
namespace
{

constexpr std::array<ShopCheatKey, 10> KONAMI_CODE = {
    ShopCheatKey::Up, ShopCheatKey::Up, ShopCheatKey::Down, ShopCheatKey::Down,
    ShopCheatKey::Left, ShopCheatKey::Right, ShopCheatKey::Left, ShopCheatKey::Right,
    ShopCheatKey::B, ShopCheatKey::A,
};
constexpr int KONAMI_WINDOW_FRAMES = 300;

}

int ShopModel::selected_item() const noexcept
{
    return _selected_item;
}

int ShopModel::price() const noexcept
{
    const ShopItemSpec* item = shop_item_spec(_selected_item);
    return item ? item->price : 0;
}

bool ShopModel::sold_out(const FlowModel& flow) const noexcept
{
    return flow.shop_item_owned(_selected_item);
}

void ShopModel::next() noexcept
{
    _selected_item = (_selected_item + 1) % shop_item_count();
}

void ShopModel::previous() noexcept
{
    _selected_item = (_selected_item + shop_item_count() - 1) % shop_item_count();
}

void ShopModel::move_left() noexcept
{
    if(_selected_item % 4 > 0)
    {
        --_selected_item;
    }
}

void ShopModel::move_right() noexcept
{
    if(_selected_item % 4 < 3)
    {
        ++_selected_item;
    }
}

void ShopModel::move_up() noexcept
{
    if(_selected_item >= 4)
    {
        _selected_item -= 4;
    }
}

void ShopModel::move_down() noexcept
{
    if(_selected_item + 4 < shop_item_count())
    {
        _selected_item += 4;
    }
}

void ShopModel::select(int slot) noexcept
{
    if(slot >= 0 && slot < shop_item_count())
    {
        _selected_item = slot;
    }
}

ShopPurchaseResult ShopModel::purchase(FlowModel& flow) const noexcept
{
    return flow.purchase_shop_item(_selected_item);
}

ShopCheatResult ShopModel::push_cheat_key(ShopCheatKey key, int frame) noexcept
{
    if(_cheat_index > 0 && frame - _cheat_start_frame > KONAMI_WINDOW_FRAMES)
    {
        reset_cheat();
    }

    if(key == KONAMI_CODE[_cheat_index])
    {
        if(_cheat_index == 0)
        {
            _cheat_start_frame = frame;
        }

        ++_cheat_index;
        if(_cheat_index == int(KONAMI_CODE.size()))
        {
            reset_cheat();
            return ShopCheatResult::Completed;
        }
        return ShopCheatResult::Progressed;
    }

    // A mismatched Up can immediately become the first key of a fresh code.
    if(key == KONAMI_CODE[0])
    {
        _cheat_index = 1;
        _cheat_start_frame = frame;
        return ShopCheatResult::Progressed;
    }

    reset_cheat();
    return ShopCheatResult::NoProgress;
}

void ShopModel::reset_cheat() noexcept
{
    _cheat_index = 0;
    _cheat_start_frame = 0;
}

}
