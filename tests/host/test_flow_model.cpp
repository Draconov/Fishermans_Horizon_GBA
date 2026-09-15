#include <cassert>

#include "flow_model.h"

namespace
{

void advance_title(fh::FlowModel& model, int updates)
{
    for(int index = 0; index < updates; ++index)
    {
        model.update_title_animation();
    }
}

void advance_map(fh::FlowModel& model, int updates)
{
    for(int index = 0; index < updates; ++index)
    {
        model.update_map_markers();
    }
}

}

int main()
{
    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(model.state() == fh::GameState::Title);
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.state() == fh::GameState::Map);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = false;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.state() == fh::GameState::Event);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Options);
        assert(model.state() == fh::GameState::Options);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(model.title_sea_tile() == 112);
        advance_title(model, 1);
        assert(model.title_sea_tile() == 113);
        advance_title(model, 12);
        assert(model.title_sea_tile() == 114);
        advance_title(model, 12);
        assert(model.title_sea_tile() == 113);
        advance_title(model, 12);
        assert(model.title_sea_tile() == 112);
        advance_title(model, 12);
        assert(model.title_sea_tile() == 112);
        assert(model.title_ticks() == 0);
        advance_title(model, 1);
        assert(model.title_sea_tile() == 113);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.handle_map_command(fh::MapCommand::Back);
        assert(model.state() == fh::GameState::Title);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Fishing);
        assert(model.fishing_pool() == 1);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.club_card = false;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(! model.map_target_enabled(fh::MapTarget::River));
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.map_spot_a_tile() == 100);
        assert(model.map_spot_b_tile() == 102);
        advance_map(model, 10);
        assert(model.map_spot_a_tile() == 100);
        assert(model.map_spot_b_tile() == 102);
        advance_map(model, 1);
        assert(model.map_spot_a_tile() == 101);
        assert(model.map_spot_b_tile() == 103);
        advance_map(model, 10);
        assert(model.map_spot_a_tile() == 100);
        assert(model.map_spot_b_tile() == 102);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
        model.handle_map_command(fh::MapCommand::NextTarget);
        assert(model.selected_map_target() == fh::MapTarget::Pier);
        model.handle_map_command(fh::MapCommand::NextTarget);
        assert(model.selected_map_target() == fh::MapTarget::Shop);
        // River/Ocean/Cave/Catalog are skipped while locked.
        model.handle_map_command(fh::MapCommand::NextTarget);
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Fishing);
        model.handle_fishing_back();
        assert(model.state() == fh::GameState::Map);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(model.money() == 10);
        assert(model.current_rod() == 0);
        assert(model.equipped_bait() == 0);
        assert(model.bait_owned(0));
        for(int bait = 1; bait < 7; ++bait)
        {
            assert(! model.bait_owned(bait));
        }
        for(int fish = 1; fish <= 44; ++fish)
        {
            assert(! model.catalog_has_fish(fish));
        }

        model.apply_fishing_reward(3, 1);
        assert(model.money() == 11);
        assert(model.catalog_has_fish(3));
        assert(! model.catalog_has_fish(2));

        model.apply_fishing_reward(41, 25);
        assert(model.money() == 36);
        assert(model.catalog_has_fish(41));

        model.apply_fishing_reward(40, 5000);
        assert(model.money() == 999);
        assert(model.catalog_has_fish(40));
        model.apply_fishing_reward(0, 10);
        model.apply_fishing_reward(45, 10);
        assert(model.money() == 999);
    }


    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.bait_owned = {true, false, true, false, false, true, false};
        progress.equipped_bait = 0;
        fh::FlowModel model(progress);
        model.complete_intro();
        assert(model.cycle_owned_bait() == 2);
        assert(model.equipped_bait() == 2);
        assert(model.cycle_owned_bait() == 5);
        assert(model.cycle_owned_bait() == 0);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.handle_map_command(fh::MapCommand::NextTarget); // Pier
        assert(model.selected_map_target() == fh::MapTarget::Pier);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Fishing);
        assert(model.fishing_pool() == 2);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.club_card = true;
        progress.old_boat = true;
        progress.ancient_map = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        for(int expected_pool = 2; expected_pool <= 5; ++expected_pool)
        {
            model.handle_map_command(fh::MapCommand::NextTarget);
            if(expected_pool == 3)
            {
                // Shop sits between Pier and River in the recovered target order.
                model.handle_map_command(fh::MapCommand::NextTarget);
            }
            if(expected_pool == 4 || expected_pool == 5)
            {
                // Already on previous fishing target; one Next reaches the next area.
            }
            const fh::MapTarget target = model.selected_map_target();
            if(target == fh::MapTarget::Shop)
            {
                model.handle_map_command(fh::MapCommand::NextTarget);
            }
            model.handle_map_command(fh::MapCommand::Confirm);
            assert(model.state() == fh::GameState::Fishing);
            assert(model.fishing_pool() == expected_pool);
            model.handle_fishing_back();
        }
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.handle_map_command(fh::MapCommand::NextTarget); // Pier
        model.handle_map_command(fh::MapCommand::NextTarget); // Shop
        assert(model.selected_map_target() == fh::MapTarget::Shop);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Shop);
        model.handle_shop_back();
        assert(model.state() == fh::GameState::Map);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.catalog = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        // Catalog is the previous enabled target when only its purchase flag is unlocked.
        model.handle_map_command(fh::MapCommand::PreviousTarget);
        assert(model.selected_map_target() == fh::MapTarget::Catalog);
        model.handle_map_command(fh::MapCommand::Confirm);
        assert(model.state() == fh::GameState::Catalog);
        model.handle_catalog_back(false);
        assert(model.state() == fh::GameState::Map);
    }


    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.money = 500;
        progress.bait_owned[2] = true;
        progress.character_owned[2] = true;
        fh::FlowModel model(progress);
        model.complete_intro();
        const auto initial_revision = model.progress_revision();

        model.update_title_animation();
        assert(model.progress_revision() == initial_revision);
        model.handle_title_command(fh::TitleCommand::Play);
        model.update_map_markers();
        model.handle_map_command(fh::MapCommand::NextTarget);
        assert(model.progress_revision() == initial_revision);

        model.toggle_sound_option();
        assert(model.progress_revision() == initial_revision + 1);
        (void) model.cycle_owned_bait();
        assert(model.progress_revision() == initial_revision + 2);
        (void) model.cycle_owned_character();
        assert(model.progress_revision() == initial_revision + 3);

        const auto before_reward = model.progress_revision();
        model.apply_fishing_reward(1, 5);
        assert(model.progress_revision() == before_reward + 1);
        const auto before_duplicate_zero = model.progress_revision();
        model.apply_fishing_reward(1, 0);
        assert(model.progress_revision() == before_duplicate_zero);

        const auto before_purchase = model.progress_revision();
        assert(model.purchase_shop_item(0) == fh::ShopPurchaseResult::Purchased);
        assert(model.progress_revision() == before_purchase + 1);
        const auto before_sold_out = model.progress_revision();
        assert(model.purchase_shop_item(0) == fh::ShopPurchaseResult::SoldOut);
        assert(model.progress_revision() == before_sold_out);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = false;
        fh::FlowModel model(progress);
        model.complete_intro();
        const auto revision = model.progress_revision();
        model.handle_title_command(fh::TitleCommand::Play);
        model.complete_event();
        assert(model.progress_revision() == revision + 1);
        assert(model.progress_state().prologue_complete);
    }


    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.club_card = true;
        progress.old_boat = true;
        progress.ancient_map = true;
        progress.catalog = true;
        progress.character_owned = {true, true, true, false, false, false};
        progress.current_character = 0;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);

        // Character cycling is directional and skips locked characters.
        assert(model.cycle_owned_character(1) == 1);
        assert(model.cycle_owned_character(-1) == 0);
        assert(model.cycle_owned_character(-1) == 2);
        assert(model.cycle_owned_character(1) == 0);

        // Spatial map navigation follows the visible map graph, not a flat list.
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
        model.handle_map_command(fh::MapCommand::Left);
        assert(model.selected_map_target() == fh::MapTarget::Shop);
        model.handle_map_command(fh::MapCommand::Down);
        assert(model.selected_map_target() == fh::MapTarget::Pier);
        model.handle_map_command(fh::MapCommand::Left);
        assert(model.selected_map_target() == fh::MapTarget::Cave);
        model.handle_map_command(fh::MapCommand::Down);
        assert(model.selected_map_target() == fh::MapTarget::Ocean);
        model.handle_map_command(fh::MapCommand::Up);
        assert(model.selected_map_target() == fh::MapTarget::Pier);
        model.handle_map_command(fh::MapCommand::Right);
        assert(model.selected_map_target() == fh::MapTarget::River);
        model.handle_map_command(fh::MapCommand::Left);
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);

        // Catalog is a START shortcut, not a map selection target.
        model.open_catalog_from_map();
        assert(model.state() == fh::GameState::Catalog);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.catalog = false;
        fh::FlowModel model(progress);
        model.complete_intro();
        model.handle_title_command(fh::TitleCommand::Play);
        model.open_catalog_from_map();
        assert(model.state() == fh::GameState::Map);

        // Locked spatial neighbors don't become selectable.
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
        model.handle_map_command(fh::MapCommand::Right); // River is locked.
        assert(model.selected_map_target() == fh::MapTarget::CrystalLake);
    }

    return 0;
}

