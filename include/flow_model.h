#ifndef FH_FLOW_MODEL_H
#define FH_FLOW_MODEL_H

#include <array>
#include <cstdint>

#include "game_state.h"
#include "map_content.h"
#include "progression_content.h"

namespace fh
{

enum class TitleCommand
{
    None,
    Play,
    Options,
};

enum class MapCommand
{
    None,
    PreviousTarget,
    NextTarget,
    Left,
    Right,
    Up,
    Down,
    Confirm,
    Back,
};

struct ProgressState
{
    bool prologue_complete = false;
    int sound = 1;
    bool club_card = false;
    bool old_boat = false;
    bool ancient_map = false;
    bool catalog = false;
    bool captains_hat = false;
    bool beach_ball = false;
    bool car_keys = false;
    Region active_region = Region::MariMari;
    int money = 10;
    int current_character = 0;
    int current_rod = 0;
    int equipped_bait = 0;
    std::array<bool, 7> bait_owned = {true, false, false, false, false, false, false};
    std::array<bool, 3> rod_owned = {true, false, false};
    std::array<bool, 6> character_owned = {true, true, false, false, false, false};
    std::array<bool, 32> shop2_owned = {};
    std::array<bool, 54> fish_catalog = {};
};

class FlowModel
{
public:
    explicit FlowModel(ProgressState progress) noexcept;

    [[nodiscard]] GameState state() const noexcept;
    [[nodiscard]] int fishing_pool() const noexcept;
    [[nodiscard]] int sound_option() const noexcept;
    [[nodiscard]] bool prologue_complete() const noexcept;
    [[nodiscard]] int event_id() const noexcept;
    [[nodiscard]] ProgressState progress_state() const noexcept;
    [[nodiscard]] std::uint32_t progress_revision() const noexcept;
    [[nodiscard]] Region active_region() const noexcept;
    [[nodiscard]] ShopId active_shop() const noexcept;

    void complete_intro() noexcept;
    void handle_title_command(TitleCommand command) noexcept;
    void update_title_animation() noexcept;
    [[nodiscard]] int title_sea_tile() const noexcept;
    [[nodiscard]] int title_ticks() const noexcept;

    void handle_map_command(MapCommand command) noexcept;
    void open_catalog_from_map() noexcept;
    void update_map_markers() noexcept;
    void handle_fishing_back() noexcept;
    void handle_shop_back() noexcept;
    void handle_options_back() noexcept;
    void handle_catalog_back(bool catalog_complete) noexcept;
    void toggle_sound_option() noexcept;
    void begin_event_dialog(int event_id) noexcept;
    void complete_event() noexcept;
    [[nodiscard]] MapTarget selected_map_target() const noexcept;
    [[nodiscard]] bool map_target_enabled(MapTarget target) const noexcept;
    [[nodiscard]] int map_spot_a_tile() const noexcept;
    [[nodiscard]] int map_spot_b_tile() const noexcept;

    [[nodiscard]] int money() const noexcept;
    [[nodiscard]] int current_character() const noexcept;
    [[nodiscard]] int current_rod() const noexcept;
    [[nodiscard]] int equipped_bait() const noexcept;
    [[nodiscard]] bool bait_owned(int bait) const noexcept;
    [[nodiscard]] bool rod_owned(int rod) const noexcept;
    [[nodiscard]] bool character_owned(int character) const noexcept;
    [[nodiscard]] int cycle_owned_character(int direction = 1) noexcept;

    [[nodiscard]] bool shop_item_owned(ShopId shop, int slot) const noexcept;
    [[nodiscard]] bool shop_item_locked(ShopId shop, int slot) const noexcept;
    [[nodiscard]] bool shop_item_purchasable(ShopId shop, int slot) const noexcept;
    [[nodiscard]] ShopPurchaseResult purchase_shop_item(ShopId shop, int slot) noexcept;

    // Compatibility helpers for the Mari-Mari shop.
    [[nodiscard]] bool shop_item_owned(int slot) const noexcept;
    [[nodiscard]] bool shop_item_locked(int slot) const noexcept;
    [[nodiscard]] bool shop_item_purchasable(int slot) const noexcept;
    [[nodiscard]] ShopPurchaseResult purchase_shop_item(int slot) noexcept;

    [[nodiscard]] int cycle_owned_bait(int direction = 1) noexcept;
    [[nodiscard]] bool catalog_has_fish(int fish_number) const noexcept;
    void apply_fishing_reward(int fish_number, int reward) noexcept;
    void grant_money(int amount) noexcept;

private:
    void _select_relative_map_target(int direction) noexcept;
    void _select_spatial_map_target(MapCommand command) noexcept;
    void _activate_selected_map_target() noexcept;

    ProgressState _progress;
    GameState _state = GameState::Intro;
    int _fishing_pool = 0;
    int _event_id = 0;
    int _title_ticks = 0;
    int _title_sea_tile = 112;
    int _map_ticks = 0;
    int _map_spot_a_tile = 100;
    int _map_spot_b_tile = 102;
    MapTarget _selected_map_target = MapTarget::CrystalLake;
    ShopId _active_shop = ShopId::MariMari;
    std::uint32_t _progress_revision = 0;
};

}

#endif
