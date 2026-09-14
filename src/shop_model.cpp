#include "shop_model.h"

#include "flow_model.h"

namespace fh
{

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

}
