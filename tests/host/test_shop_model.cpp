#include <array>
#include <cassert>

#include "flow_model.h"
#include "progression_content.h"
#include "shop_model.h"

namespace
{

constexpr std::array<int, 16> EXPECTED_PRICES = {
    15, 15, 30, 45, 100, 100, 45, 120, 30, 60, 120, 20, 30, 30, 50, 100,
};

void verify_effect(int slot, const fh::FlowModel& flow)
{
    if(slot <= 5)
    {
        assert(flow.bait_owned(slot + 1));
        return;
    }

    switch(slot)
    {
    case 6:
        assert(flow.rod_owned(1));
        assert(flow.current_rod() == 1);
        break;
    case 7:
        assert(flow.rod_owned(2));
        assert(flow.current_rod() == 2);
        break;
    case 8:
        assert(flow.map_target_enabled(fh::MapTarget::Ocean));
        break;
    case 9:
        assert(flow.map_target_enabled(fh::MapTarget::River));
        break;
    case 10:
        assert(flow.map_target_enabled(fh::MapTarget::Cave));
        break;
    case 11:
        assert(flow.map_target_enabled(fh::MapTarget::Catalog));
        break;
    case 12:
        assert(flow.character_owned(2));
        break;
    case 13:
        assert(flow.character_owned(3));
        break;
    case 14:
        assert(flow.character_owned(4));
        break;
    case 15:
        assert(flow.character_owned(5));
        break;
    default:
        assert(false);
    }
}

}

int main()
{
    assert(fh::shop_item_count() == 16);
    for(int slot = 0; slot < 16; ++slot)
    {
        const fh::ShopItemSpec* item = fh::shop_item_spec(slot);
        assert(item);
        assert(item->slot == slot);
        assert(item->price == EXPECTED_PRICES[slot]);
        assert(item->name && item->name[0] != '\0');
        assert(item->description && item->description[0] != '\0');
    }
    assert(fh::shop_item_spec(-1) == nullptr);
    assert(fh::shop_item_spec(16) == nullptr);

    {
        fh::ProgressState progress;
        assert(progress.money == 10);
        assert(progress.sound == 1);
        assert(progress.current_character == 0);
        assert((progress.rod_owned == std::array<bool, 3>{true, false, false}));
        assert((progress.character_owned == std::array<bool, 6>{true, true, false, false, false, false}));
    }

    for(int slot = 0; slot < 16; ++slot)
    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.money = 999;
        fh::FlowModel flow(progress);
        if(slot == 7)
        {
            assert(flow.purchase_shop_item(6) == fh::ShopPurchaseResult::Purchased);
        }
        fh::ShopModel shop;
        shop.select(slot);

        assert(shop.selected_item() == slot);
        assert(shop.price() == EXPECTED_PRICES[slot]);
        assert(! shop.sold_out(flow));
        const int before = flow.money();
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::Purchased);
        assert(flow.money() == before - EXPECTED_PRICES[slot]);
        assert(shop.sold_out(flow));
        verify_effect(slot, flow);

        const int after = flow.money();
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::SoldOut);
        assert(flow.money() == after);
    }

    {
        fh::ProgressState progress;
        progress.money = 14;
        fh::FlowModel flow(progress);
        fh::ShopModel shop;
        shop.select(0);
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::InsufficientFunds);
        assert(flow.money() == 14);
        assert(! flow.bait_owned(1));
    }

    {
        fh::ShopModel shop;
        assert(shop.selected_item() == 0);
        shop.previous();
        assert(shop.selected_item() == 15);
        shop.next();
        assert(shop.selected_item() == 0);
        shop.select(15);
        shop.next();
        assert(shop.selected_item() == 0);
        shop.select(-1);
        assert(shop.selected_item() == 0);
        shop.select(16);
        assert(shop.selected_item() == 0);
    }

    {
        // GBA spatial navigation keeps the 4x4 Shop layout instead of treating
        // it as a single wrapping list. Edges clamp in their current row/column.
        fh::ShopModel shop;
        assert(shop.selected_item() == 0);
        shop.move_left();
        assert(shop.selected_item() == 0);
        shop.move_up();
        assert(shop.selected_item() == 0);

        shop.move_right();
        assert(shop.selected_item() == 1);
        shop.move_down();
        assert(shop.selected_item() == 5);
        shop.move_down();
        assert(shop.selected_item() == 9);
        shop.move_down();
        assert(shop.selected_item() == 13);
        shop.move_down();
        assert(shop.selected_item() == 13);

        shop.move_left();
        assert(shop.selected_item() == 12);
        shop.move_left();
        assert(shop.selected_item() == 12);
        shop.move_up();
        assert(shop.selected_item() == 8);
        shop.move_up();
        assert(shop.selected_item() == 4);
        shop.move_up();
        assert(shop.selected_item() == 0);
        shop.move_up();
        assert(shop.selected_item() == 0);

        shop.select(3);
        shop.move_right();
        assert(shop.selected_item() == 3);
        shop.select(15);
        shop.move_right();
        assert(shop.selected_item() == 15);
    }

    {
        fh::ProgressState progress;
        progress.money = 999;
        fh::FlowModel flow(progress);
        assert(flow.current_character() == 0);
        assert(flow.character_owned(0));
        assert(flow.character_owned(1));
        for(int character = 2; character < 6; ++character)
        {
            assert(! flow.character_owned(character));
        }
        assert(flow.cycle_owned_character() == 1);
        assert(flow.cycle_owned_character() == 0);

        assert(flow.purchase_shop_item(12) == fh::ShopPurchaseResult::Purchased);
        assert(flow.cycle_owned_character() == 1);
        assert(flow.cycle_owned_character() == 2);
        assert(flow.cycle_owned_character() == 0);
    }

    {
        // The original Shop hides Nova Rod until Pro Rod has been bought.
        fh::ProgressState progress;
        progress.money = 999;
        fh::FlowModel flow(progress);
        fh::ShopModel shop;
        shop.select(7);
        assert(flow.shop_item_locked(7));
        assert(! flow.shop_item_purchasable(7));
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::Locked);
        assert(! flow.rod_owned(2));

        shop.select(6);
        assert(flow.shop_item_purchasable(6));
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::Purchased);
        assert(! flow.shop_item_locked(7));
        assert(flow.shop_item_purchasable(7));
        shop.select(7);
        assert(shop.purchase(flow) == fh::ShopPurchaseResult::Purchased);
        assert(flow.rod_owned(2));
    }

    return 0;
}
