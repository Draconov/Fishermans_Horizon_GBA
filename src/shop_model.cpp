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

int shop_page_count() noexcept
{
    return (shop_item_count() + SHOP_PAGE_SIZE - 1) / SHOP_PAGE_SIZE;
}

}

int ShopModel::selected_item() const noexcept
{
    return _selected_item;
}

int ShopModel::page() const noexcept
{
    return _selected_item / SHOP_PAGE_SIZE;
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
    const int local_slot = _selected_item % SHOP_PAGE_SIZE;
    if(local_slot % SHOP_COLUMNS > 0)
    {
        --_selected_item;
    }
}

void ShopModel::move_right() noexcept
{
    const int local_slot = _selected_item % SHOP_PAGE_SIZE;
    const int candidate = _selected_item + 1;
    if(local_slot % SHOP_COLUMNS < SHOP_COLUMNS - 1 &&
       candidate < shop_item_count() && candidate / SHOP_PAGE_SIZE == page())
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
        _selected_item = (page() - 1) * SHOP_PAGE_SIZE +
                         (SHOP_PAGE_SIZE - SHOP_COLUMNS) + column;
    }
}

void ShopModel::move_down() noexcept
{
    const int current_page = page();
    const int local_slot = _selected_item % SHOP_PAGE_SIZE;
    const int column = local_slot % SHOP_COLUMNS;
    const int row = local_slot / SHOP_COLUMNS;

    if(row < (SHOP_PAGE_SIZE / SHOP_COLUMNS) - 1)
    {
        const int candidate = _selected_item + SHOP_COLUMNS;
        if(candidate < shop_item_count() && candidate / SHOP_PAGE_SIZE == current_page)
        {
            _selected_item = candidate;
        }
        return;
    }

    if(current_page + 1 < shop_page_count())
    {
        const int next_page_start = (current_page + 1) * SHOP_PAGE_SIZE;
        const int next_row_last = next_page_start + SHOP_COLUMNS - 1;
        const int last_item = shop_item_count() - 1;
        int candidate = next_page_start + column;
        if(candidate > last_item)
        {
            candidate = last_item < next_row_last ? last_item : next_row_last;
        }
        _selected_item = candidate;
    }
}

void ShopModel::next_page() noexcept
{
    const int pages = shop_page_count();
    if(pages > 0)
    {
        _selected_item = ((page() + 1) % pages) * SHOP_PAGE_SIZE;
    }
}

void ShopModel::previous_page() noexcept
{
    const int pages = shop_page_count();
    if(pages > 0)
    {
        _selected_item = ((page() + pages - 1) % pages) * SHOP_PAGE_SIZE;
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
