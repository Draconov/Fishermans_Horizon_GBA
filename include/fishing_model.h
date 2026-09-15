#ifndef FH_FISHING_MODEL_H
#define FH_FISHING_MODEL_H

#include <array>

#include "fishing_content.h"

namespace fh
{

enum class FishingState : int
{
    Init = 0,
    Stand = 1,
    Recoil = 2,
    GetReadyToThrow = 3,
    Throw = 4,
    BaitInWater = 5,
    FishInLine = 6,
    LineBreak = 7,
    FishCatch = 8,
    Reward = 9,
};

enum class FishingDialog
{
    None,
    Catch,
    LineBreak,
};

enum class FishingSoundEvent
{
    None,
    NextPage,
    Throw,
    LineBreak,
    Coin,
    FishCatchBait,
    Water,
    Fanfare,
    Coil,
};

struct FishingInput
{
    bool rod_held = false;
    bool confirm_dialog = false;
    bool back = false;
    bool cancel_cast = false;
};

struct FishingReward
{
    bool valid = false;
    int fish_number = 0;
    int amount = 0;
};


class FishingModel
{
public:
    explicit FishingModel(int rod_index = 0, int equipped_bait = 0) noexcept;
    FishingModel(int pool, int rod_index, int equipped_bait) noexcept;

    void update(const FishingInput& input, int random_roll) noexcept;
    [[nodiscard]] FishingReward take_reward() noexcept;
    [[nodiscard]] FishingSoundEvent take_sound_event() noexcept;
    void set_equipped_bait(int equipped_bait) noexcept;

    [[nodiscard]] FishingState state() const noexcept;
    [[nodiscard]] int pool() const noexcept;
    [[nodiscard]] int rod_index() const noexcept;
    [[nodiscard]] int ticks() const noexcept;
    [[nodiscard]] int sea_tile() const noexcept;
    [[nodiscard]] bool needs_random_roll() const noexcept;
    [[nodiscard]] int meter_x() const noexcept;
    [[nodiscard]] float line_distance() const noexcept;
    [[nodiscard]] int line_x1() const noexcept;
    [[nodiscard]] int line_y1() const noexcept;
    [[nodiscard]] int line_y2() const noexcept;
    [[nodiscard]] int stick_strength() const noexcept;
    [[nodiscard]] int throw_delay() const noexcept;
    [[nodiscard]] int equipped_bait() const noexcept;
    [[nodiscard]] int bait_move_points() const noexcept;
    [[nodiscard]] int bait_movement_type() const noexcept;
    [[nodiscard]] int bait_x() const noexcept;
    [[nodiscard]] int bait_y() const noexcept;
    [[nodiscard]] int bait_sprite() const noexcept;
    [[nodiscard]] int current_fish_number() const noexcept;
    [[nodiscard]] int current_fish_strength() const noexcept;
    [[nodiscard]] int current_stamina() const noexcept;
    [[nodiscard]] int current_reward() const noexcept;
    [[nodiscard]] const char* current_fish_name() const noexcept;
    [[nodiscard]] bool dialog_alive() const noexcept;
    [[nodiscard]] FishingDialog dialog_kind() const noexcept;
    [[nodiscard]] const char* dialog_fish_name() const noexcept;
    [[nodiscard]] bool exit_requested() const noexcept;
    void clear_exit_request() noexcept;

    [[nodiscard]] int char_frame() const noexcept;
    [[nodiscard]] int stick_frame() const noexcept;
    [[nodiscard]] int splash_frame() const noexcept;
    [[nodiscard]] int coin_frame() const noexcept;
    [[nodiscard]] int coin_y() const noexcept;
    [[nodiscard]] bool draw_line() const noexcept;
    [[nodiscard]] bool draw_bait() const noexcept;
    [[nodiscard]] bool draw_splash() const noexcept;
    [[nodiscard]] bool draw_coin() const noexcept;

    [[nodiscard]] static const FishSpec* crystal_lake_fish_for_roll(int roll) noexcept;

private:
    struct FishRuntime
    {
        int lure_timer = 0;
        int strength = 0;
        int stamina = 0;
        int critical_stamina = 0;
        int rest_count = 0;
        int current_stamina = 0;
        int current_rest_count = 0;
        int rest_ticks = 0;
        bool rest = false;
    };

    void _reset_vars() noexcept;
    void _set_bait() noexcept;
    void _update_bait_lure(bool rod_held) noexcept;
    void _try_lure(int roll) noexcept;
    void _update_current_fish_stamina() noexcept;
    void _set_delay() noexcept;
    void _update_sea() noexcept;
    void _emit_sound(FishingSoundEvent event) noexcept;

    void _state_init(const FishingInput& input) noexcept;
    void _state_stand(const FishingInput& input) noexcept;
    void _state_get_ready(const FishingInput& input) noexcept;
    void _state_throw() noexcept;
    void _state_bait_in_water(const FishingInput& input, int random_roll) noexcept;
    void _state_fish_in_line(const FishingInput& input) noexcept;
    void _state_recoil() noexcept;
    void _state_fish_catch(const FishingInput& input) noexcept;
    void _state_line_break(const FishingInput& input) noexcept;
    void _state_reward() noexcept;

    std::array<FishRuntime, 9> _fish_runtime{};
    int _pool = 1;
    int _rod_index = 0;
    int _equipped_bait = 0;
    int _stick_strength = 10;
    FishingState _state = FishingState::Init;
    int _ticks = 0;
    int _odd_ticks = 0;
    int _random_ticks = 0;
    int _random_number = 0;
    int _sea_ticks = 0;
    int _sea_tile = 112;
    int _delay = 0;
    int _meter_x = 37;
    float _line_distance = 50.0f;
    int _line_x1 = 50;
    int _line_y1 = 50;
    int _line_y2 = 128;
    int _char_frame = 0;
    int _stick_frame = 0;
    int _splash_frame = 0;
    int _coin_frame = 0;
    int _coin_y = 0;
    bool _draw_line = false;
    bool _draw_bait = true;
    bool _draw_splash = false;
    bool _draw_coin = false;
    int _bait_ticks = 0;
    int _bait_move_points = 0;
    int _bait_movement_type = 0;
    int _bait_x = 48;
    int _bait_y = 72;
    int _bait_sprite = 11;
    bool _fish_online = false;
    int _current_fish_index = -1;
    int _current_fish_number = 0;
    int _fish_strength = 0;
    int _reward = 0;
    FishingDialog _dialog_kind = FishingDialog::None;
    bool _dialog_alive = false;
    bool _exit_requested = false;
    FishingReward _pending_reward{};
    std::array<FishingSoundEvent, 8> _sound_events{};
    int _sound_event_count = 0;
};

}

#endif
