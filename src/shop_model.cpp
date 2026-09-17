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
constexpr int SHOP_PAGE_SIZE = 16;
constexpr int SHOP_COLUMNS = 4;

}

ShopModel::ShopModel(ShopId shop) noexcept :
    _shop_id(shop)
{
}

ShopId ShopModel::shop_id() const noexcept { return _shop_id; }
int ShopModel::selected_item() const noexcept { return _selected_item; }
int ShopModel::page() const noexcept { return _selected_item / SHOP_PAGE_SIZE; }

int ShopModel::_item_count() const noexcept { return shop_item_count(_shop_id); }
int ShopModel::_page_count() const noexcept
{
    const int count = _item_count();
    return count > 0 ? (count + SHOP_PAGE_SIZE - 1) / SHOP_PAGE_SIZE : 0;
}

int ShopModel::price() const noexcept
{
    const ShopItemSpec* item = shop_item_spec(_shop_id, _selected_item);
    return item ? item->price : 0;
}

bool ShopModel::sold_out(const FlowModel& flow) const noexcept
{
    return flow.shop_item_owned(_shop_id, _selected_item);
}

void ShopModel::next() noexcept
{
    const int count = _item_count();
    if(count > 0) _selected_item = (_selected_item + 1) % count;
}

void ShopModel::previous() noexcept
{
    const int count = _item_count();
    if(count > 0) _selected_item = (_selected_item + count - 1) % count;
}

void ShopModel::move_left() noexcept
{
    const int local_slot = _selected_item % SHOP_PAGE_SIZE;
    if(local_slot % SHOP_COLUMNS > 0) --_selected_item;
}

void ShopModel::move_right() noexcept
{
    const int local_slot = _selected_item % SHOP_PAGE_SIZE;
    const int candidate = _selected_item + 1;
    if(local_slot % SHOP_COLUMNS < SHOP_COLUMNS - 1 && candidate < _item_count() && candidate / SHOP_PAGE_SIZE == page())
    {
        _selected_item = candidate;
    }
}

void ShopModel::move_up() noexcept
{
    const int local_slot = _selected_item % SHOP_PAGE_SIZE;
    const int column = local_slot % SHOP_COLUMNS;
    const int row = local_slot / SHOP_COLUMNS;
    if(row > 0)
    {
        _selected_item -= SHOP_COLUMNS;
        return;
    }
    if(page() > 0)
    {
        _selected_item = (page() - 1) * SHOP_PAGE_SIZE + (SHOP_PAGE_SIZE - SHOP_COLUMNS) + column;
        const int count = _item_count();
        if(_selected_item >= count) _selected_item = count - 1;
    }
}

void ShopModel::move_down() noexcept
{
    const int current_page = page();
    const int local_slot = _selected_item % SHOP_PAGE_SIZE;
    const int column = local_slot % SHOP_COLUMNS;
    const int row = local_slot / SHOP_COLUMNS;
    const int count = _item_count();

    if(row < (SHOP_PAGE_SIZE / SHOP_COLUMNS) - 1)
    {
        const int candidate = _selected_item + SHOP_COLUMNS;
        if(candidate < count && candidate / SHOP_PAGE_SIZE == current_page) _selected_item = candidate;
        return;
    }

    if(current_page + 1 < _page_count())
    {
        const int next_page_start = (current_page + 1) * SHOP_PAGE_SIZE;
        int candidate = next_page_start + column;
        if(candidate >= count) candidate = count - 1;
        _selected_item = candidate;
    }
}

void ShopModel::next_page() noexcept
{
    const int pages = _page_count();
    if(pages > 0) _selected_item = ((page() + 1) % pages) * SHOP_PAGE_SIZE;
}

void ShopModel::previous_page() noexcept
{
    const int pages = _page_count();
    if(pages > 0) _selected_item = ((page() + pages - 1) % pages) * SHOP_PAGE_SIZE;
}

void ShopModel::select(int slot) noexcept
{
    if(slot >= 0 && slot < _item_count()) _selected_item = slot;
}

ShopPurchaseResult ShopModel::purchase(FlowModel& flow) const noexcept
{
    return flow.purchase_shop_item(_shop_id, _selected_item);
}

ShopCheatResult ShopModel::push_cheat_key(ShopCheatKey key, int frame) noexcept
{
    if(_cheat_index > 0 && frame - _cheat_start_frame > KONAMI_WINDOW_FRAMES) reset_cheat();
    if(key == KONAMI_CODE[_cheat_index])
    {
        if(_cheat_index == 0) _cheat_start_frame = frame;
        ++_cheat_index;
        if(_cheat_index == int(KONAMI_CODE.size()))
        {
            reset_cheat();
            return ShopCheatResult::Completed;
        }
        return ShopCheatResult::Progressed;
    }
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
