#include "fishing_model.h"

namespace fh
{
namespace
{

constexpr std::array<int, 7> BAIT_SPRITES = {11, 75, 13, 77, 88, 90, 92};

}

FishingModel::FishingModel(int rod_index, int equipped_bait) noexcept :
    FishingModel(1, rod_index, equipped_bait)
{
}

FishingModel::FishingModel(int pool, int rod_index, int equipped_bait) noexcept :
    _pool(pool),
    _rod_index(rod_index),
    _equipped_bait(equipped_bait)
{
    if(_pool < 1 || _pool > fishing_area_count())
    {
        _pool = 1;
    }
    if(_rod_index < 0 || _rod_index > 2)
    {
        _rod_index = 0;
    }
    if(_equipped_bait < 0 || _equipped_bait > 6)
    {
        _equipped_bait = 0;
    }
    _stick_strength = 10 + _rod_index * 2;
    for(int index = 0; index < int(_fish_runtime.size()); ++index)
    {
        const FishSpec& spec = *fish_for_roll(_pool, index + 1);
        FishRuntime& runtime = _fish_runtime[index];
        switch(spec.difficulty)
        {
        case 0:
            runtime.strength = 4; runtime.stamina = 1; runtime.critical_stamina = 1; runtime.rest_count = 0;
            break;
        case 1:
            runtime.strength = 7; runtime.stamina = 600; runtime.critical_stamina = 150; runtime.rest_count = 3;
            break;
        case 2:
            runtime.strength = 8; runtime.stamina = 700; runtime.critical_stamina = 200; runtime.rest_count = 4;
            break;
        case 3:
            runtime.strength = 9; runtime.stamina = 1000; runtime.critical_stamina = 250; runtime.rest_count = 6;
            break;
        default:
            runtime.strength = 10; runtime.stamina = 1200; runtime.critical_stamina = 300; runtime.rest_count = 8;
            break;
        }
    }
    _reset_vars();
    _state = FishingState::Init;
}

void FishingModel::update(const FishingInput& input, int random_roll) noexcept
{
    ++_ticks;
    if(input.confirm_dialog && _dialog_alive)
    {
        _dialog_alive = false;
    }

    switch(_state)
    {
    case FishingState::Init:
        _state_init(input);
        break;
    case FishingState::Stand:
        _state_stand(input);
        break;
    case FishingState::Recoil:
        _state_recoil();
        break;
    case FishingState::GetReadyToThrow:
        _state_get_ready(input);
        break;
    case FishingState::Throw:
        _state_throw();
        break;
    case FishingState::BaitInWater:
        _state_bait_in_water(input, random_roll);
        break;
    case FishingState::FishInLine:
        _state_fish_in_line(input);
        break;
    case FishingState::LineBreak:
        _state_line_break(input);
        break;
    case FishingState::FishCatch:
        _state_fish_catch(input);
        break;
    case FishingState::Reward:
        _state_reward();
        break;
    }

    if(input.back && ! _dialog_alive && (_state == FishingState::Stand || _state == FishingState::Init))
    {
        _exit_requested = true;
    }

    _update_sea();
}

FishingReward FishingModel::take_reward() noexcept
{
    FishingReward result = _pending_reward;
    _pending_reward = {};
    return result;
}

FishingSoundEvent FishingModel::take_sound_event() noexcept
{
    if(_sound_event_count == 0)
    {
        return FishingSoundEvent::None;
    }

    const FishingSoundEvent result = _sound_events[0];
    for(int index = 1; index < _sound_event_count; ++index)
    {
        _sound_events[index - 1] = _sound_events[index];
    }
    --_sound_event_count;
    return result;
}

void FishingModel::set_equipped_bait(int equipped_bait) noexcept
{
    if(equipped_bait < 0 || equipped_bait > 6)
    {
        return;
    }
    _equipped_bait = equipped_bait;
    _set_bait();
    _emit_sound(FishingSoundEvent::NextPage);
}

const FishSpec* FishingModel::crystal_lake_fish_for_roll(int roll) noexcept
{
    return fish_for_roll(1, roll);
}

void FishingModel::_reset_vars() noexcept
{
    _ticks = 0;
    _draw_line = false;
    _draw_splash = false;
    _draw_bait = true;
    _draw_coin = false;
    _char_frame = 0;
    _stick_frame = 0;
    _splash_frame = 0;
    _coin_frame = 0;
    _line_x1 = 50;
    _line_y1 = 50;
    _line_distance = 50.0f;
    _line_y2 = 128;
    _meter_x = 37;
    _delay = 0;
    _odd_ticks = 0;
    _random_ticks = 0;
    _reward = 0;
    _fish_online = false;
    _current_fish_index = -1;
    _current_fish_number = 0;
    _fish_strength = 0;
    _dialog_kind = FishingDialog::None;
    _dialog_alive = false;
    _set_bait();
}

void FishingModel::_set_bait() noexcept
{
    _bait_x = 48;
    _bait_y = 72;
    _bait_move_points = 0;
    _bait_movement_type = 0;
    _bait_sprite = BAIT_SPRITES[_equipped_bait];
}

void FishingModel::_update_bait_lure(bool rod_held) noexcept
{
    ++_bait_ticks;
    if(rod_held)
    {
        if(_bait_ticks % 12 == 0)
        {
            ++_bait_move_points;
            if(_bait_move_points > 10)
            {
                _bait_move_points = 10;
            }
        }
    }
    else if(_bait_ticks % 24 == 0 && _bait_move_points > 0)
    {
        --_bait_move_points;
    }

    if(_bait_move_points == 0)
    {
        _bait_movement_type = 0;
    }
    else if(_bait_move_points == 10)
    {
        _bait_movement_type = 2;
    }
    else
    {
        _bait_movement_type = 1;
    }
}

void FishingModel::_try_lure(int roll) noexcept
{
    const FishSpec* spec = fish_for_roll(_pool, roll);
    if(! spec)
    {
        return;
    }
    const int index = roll - 1;
    FishRuntime& runtime = _fish_runtime[index];
    const bool bait_matches = _equipped_bait == spec->bait || _equipped_bait == 6 || spec->bait == 7;
    const bool qualifies = bait_matches && _bait_movement_type == spec->movement && _line_distance > float(spec->distance);
    if(! qualifies)
    {
        runtime.lure_timer = 0;
        return;
    }

    ++runtime.lure_timer;
    if(runtime.lure_timer == 10)
    {
        _fish_online = true;
        _current_fish_index = index;
        _current_fish_number = spec->number;
        _fish_strength = runtime.strength;
        runtime.current_stamina = runtime.stamina;
        runtime.current_rest_count = runtime.rest_count;
        runtime.rest_ticks = 0;
        runtime.rest = false;
        _bait_sprite = spec->sprite;
        _reward = spec->reward;
        _ticks = 0;
    }
}

void FishingModel::_update_current_fish_stamina() noexcept
{
    if(_current_fish_index < 0)
    {
        return;
    }
    FishRuntime& fish = _fish_runtime[_current_fish_index];
    const FishSpec& spec = *fish_for_roll(_pool, _current_fish_index + 1);

    if(fish.current_stamina == 0)
    {
        _fish_strength = fish.strength - 3;
        return;
    }

    if(fish.rest)
    {
        ++fish.rest_ticks;
        ++fish.current_stamina;
        if(fish.current_stamina > fish.stamina)
        {
            fish.current_stamina = fish.stamina;
            _fish_strength = fish.strength;
            fish.rest = false;
            fish.rest_ticks = 0;
        }
        if(_line_distance < float(spec.distance + 80) && fish.rest_ticks > 160)
        {
            _fish_strength = fish.strength;
            fish.rest = false;
            fish.rest_ticks = 0;
        }
        return;
    }

    --fish.current_stamina;
    if(fish.current_stamina < 0)
    {
        fish.current_stamina = 0;
    }
    if(fish.current_rest_count > 0 && fish.current_stamina < fish.critical_stamina)
    {
        fish.rest = true;
        _fish_strength = fish.strength - 3;
        --fish.current_rest_count;
    }
}

void FishingModel::_set_delay() noexcept
{
    _delay = _meter_x - 37;
    if(_delay > 50)
    {
        _delay = 12;
    }
    else if(_delay > 25)
    {
        _delay = 6;
    }
    else
    {
        _delay = 0;
    }
}

void FishingModel::_state_init(const FishingInput& input) noexcept
{
    _reset_vars();
    if(! input.rod_held)
    {
        _state = FishingState::Stand;
    }
}

void FishingModel::_state_stand(const FishingInput& input) noexcept
{
    if(input.rod_held)
    {
        _ticks = 0;
        _state = FishingState::GetReadyToThrow;
    }
}

void FishingModel::_state_get_ready(const FishingInput& input) noexcept
{
    if(_ticks == 1)
    {
        _char_frame = 1;
        _stick_frame = 1;
        ++_bait_sprite;
        _bait_x = 16;
        _bait_y = 77;
    }
    if(_ticks == 4)
    {
        _char_frame = 2;
        _stick_frame = 2;
        _draw_bait = false;
    }
    if(_ticks == 7)
    {
        _char_frame = 3;
    }
    if(input.rod_held && _meter_x < 111)
    {
        _meter_x += 2;
        if(_meter_x > 111)
        {
            _meter_x = 111;
        }
    }
    if(! input.rod_held && _ticks > 9)
    {
        _ticks = 0;
        _state = FishingState::Throw;
    }
}

void FishingModel::_state_throw() noexcept
{
    if(_ticks == 1)
    {
        _char_frame = 4;
    }
    if(_ticks == 4)
    {
        _char_frame = 5;
        _stick_frame = 3;
        _emit_sound(FishingSoundEvent::Throw);
    }
    if(_ticks == 7)
    {
        _char_frame = 6;
        _stick_frame = 4;
    }
    if(_ticks == 10)
    {
        _char_frame = 7;
        _stick_frame = 5;
        _set_delay();
    }
    if(_ticks == _delay + 19)
    {
        _emit_sound(FishingSoundEvent::Water);
        _draw_splash = true;
        _splash_frame = 104;
        _line_x1 = 75;
        _line_y1 = 61;
        _line_distance = float(100 + (_meter_x - 37) * 2);
    }
    if(_ticks == _delay + 22)
    {
        _draw_line = true;
        _splash_frame = 105;
    }
    if(_ticks == _delay + 25)
    {
        _draw_line = false;
        _splash_frame = 106;
    }
    if(_ticks == _delay + 28)
    {
        _draw_line = true;
    }
    if(_ticks == _delay + 31)
    {
        _draw_line = false;
        _draw_splash = false;
    }
    if(_ticks == _delay + 34)
    {
        _draw_line = true;
    }
    if(_ticks == _delay + 37)
    {
        _char_frame = 0;
        _stick_frame = 6;
        _line_x1 = 54;
        _line_y1 = 57;
        _state = FishingState::BaitInWater;
    }
}

void FishingModel::_state_bait_in_water(const FishingInput& input, int random_roll) noexcept
{
    if(input.cancel_cast && ! _fish_online)
    {
        _ticks = 0;
        _odd_ticks = 0;
        _random_ticks = 0;
        _state = FishingState::Recoil;
        return;
    }

    ++_random_ticks;
    if(_random_ticks == 1)
    {
        _random_number = random_roll >= 0 && random_roll <= 9 ? random_roll : 0;
    }
    else if(_random_ticks > 30)
    {
        _random_ticks = 0;
    }

    if(! _fish_online)
    {
        if(input.rod_held)
        {
            _emit_sound(FishingSoundEvent::Coil);
            ++_odd_ticks;
            if(_odd_ticks % 12 == 0)
            {
                _char_frame = 0;
            }
            else if(_odd_ticks % 6 == 0)
            {
                _char_frame = 8;
            }
            if(_odd_ticks % 3 == 0)
            {
                _line_distance -= 1.0f;
            }
        }
        else if(_odd_ticks > 0)
        {
            _emit_sound(FishingSoundEvent::Coil);
            ++_odd_ticks;
            if(_odd_ticks % 12 == 0)
            {
                _char_frame = 0;
                _odd_ticks = 0;
            }
            else if(_odd_ticks % 6 == 0)
            {
                _char_frame = 8;
            }
        }

        if(_line_distance <= float(_line_x1))
        {
            _odd_ticks = 0;
            _state = FishingState::Recoil;
        }

        if(_ticks > 50)
        {
            _update_bait_lure(input.rod_held);
            _try_lure(_random_number);
        }
        if(_meter_x < 111)
        {
            _meter_x += 2;
            if(_meter_x > 111)
            {
                _meter_x = 111;
            }
        }
        return;
    }

    if(_ticks == 1)
    {
        _emit_sound(FishingSoundEvent::FishCatchBait);
    }
    if(_ticks == 4)
    {
        _char_frame = 9;
        _stick_frame = 7;
        _line_x1 = 51;
        _line_y1 = 59;
    }
    if(_ticks == 7)
    {
        _char_frame = 10;
        _stick_frame = 8;
        _line_x1 = 51;
        _line_y1 = 60;
    }
    if(_ticks == 10)
    {
        _ticks = 0;
        _fish_online = false;
        _state = FishingState::FishInLine;
    }
    if(_meter_x < 111)
    {
        _meter_x += 2;
        if(_meter_x > 111)
        {
            _meter_x = 111;
        }
    }
}

void FishingModel::_state_fish_in_line(const FishingInput& input) noexcept
{
    if(input.rod_held)
    {
        _stick_frame = 11;
        _line_x1 = 48;
        _line_y1 = 63;
        if(_ticks == 1)
        {
            _emit_sound(FishingSoundEvent::Coil);
            _char_frame = 11;
        }
        if(_ticks == 4)
        {
            _char_frame = 12;
        }
        if(_ticks == 7)
        {
            _ticks = 0;
        }
        if(_meter_x > 37 && _ticks % 2 == 0)
        {
            --_meter_x;
        }
        if(_meter_x <= 37)
        {
            _ticks = 0;
            _state = FishingState::LineBreak;
        }
        if(_fish_strength > _stick_strength)
        {
            _line_distance += float(_fish_strength - _stick_strength) * 0.1f;
        }
        if(_stick_strength > _fish_strength)
        {
            _line_distance -= float(_stick_strength - _fish_strength) * 0.1f;
        }
    }
    else
    {
        _ticks = 0;
        _char_frame = 10;
        _stick_frame = 8;
        _line_x1 = 51;
        _line_y1 = 60;
        if(_meter_x < 111)
        {
            ++_meter_x;
        }
        _line_distance += float(_fish_strength) * 0.1f;
    }

    _update_current_fish_stamina();
    if(_line_distance > 280.0f)
    {
        _ticks = 0;
        _state = FishingState::LineBreak;
    }
    if(_line_distance <= float(_line_x1))
    {
        _line_distance = float(_line_x1);
        _ticks = 0;
        _state = FishingState::FishCatch;
    }
}

void FishingModel::_state_recoil() noexcept
{
    ++_odd_ticks;
    if(_ticks % 6 == 0)
    {
        _char_frame = 8;
    }
    if(_ticks % 12 == 0)
    {
        _char_frame = 0;
    }
    if(_odd_ticks == 1)
    {
        _stick_frame = 9;
        --_bait_sprite;
        _bait_x = 53;
        _bait_y = 104;
        _draw_line = false;
        _draw_bait = true;
    }
    if(_odd_ticks == 4)
    {
        _stick_frame = 10;
        _bait_x = 48;
        _bait_y = 88;
    }
    if(_odd_ticks == 7)
    {
        _stick_frame = 0;
        _bait_y = 72;
    }
    if(_meter_x > 37)
    {
        _meter_x -= 2;
    }
    if(_meter_x < 37)
    {
        _meter_x = 37;
    }
    if(_odd_ticks > 9 && _meter_x == 37)
    {
        _state = FishingState::Init;
    }
    if(_char_frame == 0 && _odd_ticks <= 6)
    {
        _ticks = 0;
    }
}

void FishingModel::_state_fish_catch(const FishingInput&) noexcept
{
    if(_ticks == 1)
    {
        _emit_sound(FishingSoundEvent::Water);
        _draw_line = false;
        _draw_bait = true;
        _draw_splash = true;
        _char_frame = 0;
        _stick_frame = 9;
        _splash_frame = 107;
        _bait_x = 49;
        _bait_y = 104;
    }
    if(_ticks == 4)
    {
        _stick_frame = 10;
        _splash_frame = 108;
        _bait_x = 44;
        _bait_y = 88;
    }
    if(_ticks == 7)
    {
        _splash_frame = 109;
        _stick_frame = 0;
        _bait_y = 72;
    }
    if(_ticks == 10)
    {
        _draw_splash = false;
    }
    if(_ticks == 34)
    {
        _char_frame = 13;
    }
    if(_ticks == 37)
    {
        _emit_sound(FishingSoundEvent::Fanfare);
        _char_frame = 14;
    }
    if(_ticks == 43)
    {
        _dialog_kind = FishingDialog::Catch;
        _dialog_alive = true;
    }
    if(_ticks > 43 && ! _dialog_alive)
    {
        _ticks = 0;
        _state = FishingState::Reward;
    }
    if(_meter_x > 37)
    {
        _meter_x -= 2;
    }
    if(_meter_x < 37)
    {
        _meter_x = 37;
    }
}

void FishingModel::_state_line_break(const FishingInput&) noexcept
{
    if(_ticks == 1)
    {
        _emit_sound(FishingSoundEvent::LineBreak);
        _char_frame = 0;
        _stick_frame = 0;
        _meter_x = 37;
        _draw_line = false;
    }
    if(_ticks == 15)
    {
        _dialog_kind = FishingDialog::LineBreak;
        _dialog_alive = true;
    }
    if(_ticks > 15 && ! _dialog_alive)
    {
        _state = FishingState::Init;
    }
}

void FishingModel::_state_reward() noexcept
{
    if(_ticks == 1)
    {
        _char_frame = 15;
    }
    if(_ticks == 4)
    {
        _char_frame = 0;
    }
    if(_ticks == 7)
    {
        _bait_sprite = 124;
        _draw_coin = true;
        _coin_frame = 116;
        _coin_y = 76;
    }
    if(_ticks == 9)
    {
        _coin_frame = 117;
        _coin_y = 72;
    }
    if(_ticks == 11)
    {
        _coin_frame = 118;
        _coin_y = 68;
    }
    if(_ticks == 13)
    {
        _coin_frame = 117;
        _coin_y = 64;
    }
    if(_ticks == 15)
    {
        _emit_sound(FishingSoundEvent::Coin);
        _coin_frame = 116;
        _coin_y = 60;
    }
    if(_ticks == 21)
    {
        _draw_coin = false;
    }
    if(_ticks == 23)
    {
        _draw_coin = true;
    }
    if(_ticks == 25)
    {
        _draw_coin = false;
        if(! _pending_reward.valid && _current_fish_number > 0)
        {
            _pending_reward = {true, _current_fish_number, _reward};
        }
    }
    if(_ticks == 46)
    {
        _state = FishingState::Init;
    }
}


void FishingModel::_emit_sound(FishingSoundEvent event) noexcept
{
    if(event != FishingSoundEvent::None && _sound_event_count < int(_sound_events.size()))
    {
        _sound_events[_sound_event_count] = event;
        ++_sound_event_count;
    }
}

void FishingModel::_update_sea() noexcept
{
    ++_sea_ticks;
    if(_sea_ticks == 1)
    {
        _sea_tile = 113;
    }
    else if(_sea_ticks == 13)
    {
        _sea_tile = 114;
    }
    else if(_sea_ticks == 25)
    {
        _sea_tile = 113;
    }
    else if(_sea_ticks == 37)
    {
        _sea_tile = 112;
    }
    else if(_sea_ticks == 49)
    {
        _sea_ticks = 0;
    }
}

FishingState FishingModel::state() const noexcept { return _state; }
int FishingModel::pool() const noexcept { return _pool; }
int FishingModel::rod_index() const noexcept { return _rod_index; }
int FishingModel::ticks() const noexcept { return _ticks; }
int FishingModel::sea_tile() const noexcept { return _sea_tile; }
bool FishingModel::needs_random_roll() const noexcept
{
    return _state == FishingState::BaitInWater && _random_ticks == 0;
}
int FishingModel::meter_x() const noexcept { return _meter_x; }
float FishingModel::line_distance() const noexcept { return _line_distance; }
int FishingModel::line_x1() const noexcept { return _line_x1; }
int FishingModel::line_y1() const noexcept { return _line_y1; }
int FishingModel::line_y2() const noexcept { return _line_y2; }
int FishingModel::stick_strength() const noexcept { return _stick_strength; }
int FishingModel::throw_delay() const noexcept { return _delay; }
int FishingModel::equipped_bait() const noexcept { return _equipped_bait; }
int FishingModel::bait_move_points() const noexcept { return _bait_move_points; }
int FishingModel::bait_movement_type() const noexcept { return _bait_movement_type; }
int FishingModel::bait_x() const noexcept { return _bait_x; }
int FishingModel::bait_y() const noexcept { return _bait_y; }
int FishingModel::bait_sprite() const noexcept { return _bait_sprite; }
int FishingModel::current_fish_number() const noexcept { return _current_fish_number; }
int FishingModel::current_fish_strength() const noexcept { return _fish_strength; }
int FishingModel::current_stamina() const noexcept
{
    return _current_fish_index >= 0 ? _fish_runtime[_current_fish_index].current_stamina : 0;
}
int FishingModel::current_reward() const noexcept { return _reward; }
const char* FishingModel::current_fish_name() const noexcept
{
    return _current_fish_index >= 0 ? fish_for_roll(_pool, _current_fish_index + 1)->name : nullptr;
}
bool FishingModel::dialog_alive() const noexcept { return _dialog_alive; }
FishingDialog FishingModel::dialog_kind() const noexcept { return _dialog_kind; }
const char* FishingModel::dialog_fish_name() const noexcept
{
    return _dialog_kind == FishingDialog::Catch ? current_fish_name() : nullptr;
}
bool FishingModel::exit_requested() const noexcept { return _exit_requested; }
void FishingModel::clear_exit_request() noexcept { _exit_requested = false; }
int FishingModel::char_frame() const noexcept { return _char_frame; }
int FishingModel::stick_frame() const noexcept { return _stick_frame; }
int FishingModel::splash_frame() const noexcept { return _splash_frame; }
int FishingModel::coin_frame() const noexcept { return _coin_frame; }
int FishingModel::coin_y() const noexcept { return _coin_y; }
bool FishingModel::draw_line() const noexcept { return _draw_line; }
bool FishingModel::draw_bait() const noexcept { return _draw_bait; }
bool FishingModel::draw_splash() const noexcept { return _draw_splash; }
bool FishingModel::draw_coin() const noexcept { return _draw_coin; }

}
