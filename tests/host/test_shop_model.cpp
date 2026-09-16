#include <array>
#include <cassert>

#include "flow_model.h"
#include "progression_content.h"
#include "shop_model.h"

namespace
{

constexpr std::array<int, 18> EXPECTED_PRICES = {
    15, 15, 30, 45, 100, 100, 45, 120, 30, 60, 120, 20, 30, 30, 50, 100, 60, 30,
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
        assert(flow.map_target_enabled(fh::MapTarget::Waterfall));
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
    case 16:
        assert(flow.map_target_enabled(fh::MapTarget::Lagoon));
        break;
    case 17:
        assert(flow.map_target_enabled(fh::MapTarget::Beach));
        break;
    default:
        assert(false);
    }
}

}

int main()
{
    assert(fh::shop_item_count() == 18);
    for(int slot = 0; slot < 18; ++slot)
    {
        const fh::ShopItemSpec* item = fh::shop_item_spec(slot);
        assert(item);
        assert(item->slot == slot);
        assert(item->price == EXPECTED_PRICES[slot]);
        assert(item->name && item->name[0] != '\0');
        assert(item->description && item->description[0] != '\0');
    }
    assert(fh::shop_item_spec(-1) == nullptr);
    assert(fh::shop_item_spec(18) == nullptr);

    {
        fh::ProgressState progress;
        assert(progress.money == 10);
        assert(progress.sound == 1);
        assert(progress.current_character == 0);
        assert((progress.rod_owned == std::array<bool, 3>{true, false, false}));
        assert((progress.character_owned == std::array<bool, 6>{true, true, false, false, false, false}));
    }

    for(int slot = 0; slot < 18; ++slot)
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
        assert(shop.page() == 0);
        shop.previous();
        assert(shop.selected_item() == 17);
        assert(shop.page() == 1);
        shop.next();
        assert(shop.selected_item() == 0);
        shop.select(17);
        shop.next();
        assert(shop.selected_item() == 0);
        shop.select(-1);
        assert(shop.selected_item() == 0);
        shop.select(18);
        assert(shop.selected_item() == 0);

        // Shoulder-page navigation keeps the original 4x4 page intact and
        // exposes only the two active cells on custom page 2.
        shop.next_page();
        assert(shop.page() == 1);
        assert(shop.selected_item() == 16);
        shop.move_right();
        assert(shop.selected_item() == 17);
        shop.move_right();
        assert(shop.selected_item() == 17);
        shop.move_down();
        assert(shop.selected_item() == 17);
        shop.move_up();
        assert(shop.selected_item() == 17);
        shop.move_left();
        assert(shop.selected_item() == 16);
        shop.previous_page();
        assert(shop.page() == 0);
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

    {
        // Secret Shop-only Konami tracker: Up Up Down Down Left Right Left Right B A.
        // It must finish within 300 frames (5 seconds at 60 Hz).
        fh::ShopModel shop;
        using Key = fh::ShopCheatKey;
        using Result = fh::ShopCheatResult;
        assert(shop.push_cheat_key(Key::Up, 10) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Up, 20) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Down, 30) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Down, 40) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Left, 50) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Right, 60) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Left, 70) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Right, 80) == Result::Progressed);
        assert(shop.push_cheat_key(Key::B, 90) == Result::Progressed);
        assert(shop.push_cheat_key(Key::A, 100) == Result::Completed);

        // Completion resets the sequence.
        assert(shop.push_cheat_key(Key::A, 101) == Result::NoProgress);

        // Timeout resets the sequence, but a new Up can immediately restart it.
        assert(shop.push_cheat_key(Key::Up, 200) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Up, 501) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Down, 502) == Result::NoProgress);

        // Wrong keys reset; Up itself can become a fresh prefix.
        assert(shop.push_cheat_key(Key::Up, 600) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Right, 601) == Result::NoProgress);
        assert(shop.push_cheat_key(Key::Up, 602) == Result::Progressed);
        assert(shop.push_cheat_key(Key::Up, 603) == Result::Progressed);
    }

    {
        // Cheat reward uses the same progress revision/save path as real progression.
        fh::ProgressState progress;
        progress.money = 10;
        fh::FlowModel flow(progress);
        const auto revision = flow.progress_revision();
        flow.grant_money(30);
        assert(flow.money() == 40);
        assert(flow.progress_revision() == revision + 1);
        flow.grant_money(1000);
        assert(flow.money() == 999);
        const auto capped_revision = flow.progress_revision();
        flow.grant_money(30);
        assert(flow.money() == 999);
        assert(flow.progress_revision() == capped_revision);
        flow.grant_money(-1);
        assert(flow.money() == 999);
    }

    return 0;
}
