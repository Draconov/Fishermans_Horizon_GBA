#include <cassert>
#include <cmath>

#include "fishing_model.h"

namespace
{

void step(fh::FishingModel& model, bool held = false, int roll = 0, bool confirm = false, bool cancel = false)
{
    fh::FishingInput input;
    input.rod_held = held;
    input.confirm_dialog = confirm;
    input.cancel_cast = cancel;
    model.update(input, roll);
}

void advance_to_stand(fh::FishingModel& model)
{
    step(model);
    assert(model.state() == fh::FishingState::Stand);
}

void drain_sounds(fh::FishingModel& model)
{
    while(model.take_sound_event() != fh::FishingSoundEvent::None)
    {
    }
}

void cast_with_charge_frames(fh::FishingModel& model, int charge_frames)
{
    advance_to_stand(model);
    step(model, true); // STAND -> GET_READY, ticks reset to zero.
    assert(model.state() == fh::FishingState::GetReadyToThrow);

    for(int index = 0; index < charge_frames; ++index)
    {
        step(model, true);
    }

    while(model.state() == fh::FishingState::GetReadyToThrow)
    {
        step(model, false);
    }
    assert(model.state() == fh::FishingState::Throw);
}

void advance_to_bait(fh::FishingModel& model, int roll = 0)
{
    int guard = 200;
    while(model.state() == fh::FishingState::Throw && --guard)
    {
        step(model, false, roll);
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::BaitInWater);
}

void hook_boot(fh::FishingModel& model)
{
    cast_with_charge_frames(model, 37); // max meter, distance 248.
    advance_to_bait(model, 1);

    int guard = 220;
    while(model.state() == fh::FishingState::BaitInWater && --guard)
    {
        step(model, true, 1);
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishInLine);
    assert(model.current_fish_number() == 3);
}

void hook_unicuda(fh::FishingModel& model)
{
    cast_with_charge_frames(model, 37);
    advance_to_bait(model, 9);

    int guard = 300;
    int phase = 0;
    while(model.state() == fh::FishingState::BaitInWater && --guard)
    {
        // Keep bait movement at class 1 instead of letting held motion reach 10.
        const bool held = phase < 12;
        step(model, held, 9);
        phase = (phase + 1) % 28;
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishInLine);
    assert(model.current_fish_number() == 41);
}

void hook_movement_one(fh::FishingModel& model, int roll, int expected_fish_number)
{
    cast_with_charge_frames(model, 37);
    advance_to_bait(model, roll);

    int guard = 320;
    int phase = 0;
    while(model.state() == fh::FishingState::BaitInWater && --guard)
    {
        const bool held = phase < 12;
        step(model, held, roll);
        phase = (phase + 1) % 28;
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishInLine);
    assert(model.current_fish_number() == expected_fish_number);
}

void hook_movement_two(fh::FishingModel& model, int roll, int expected_fish_number)
{
    cast_with_charge_frames(model, 37);
    advance_to_bait(model, roll);

    int guard = 240;
    while(model.state() == fh::FishingState::BaitInWater && --guard)
    {
        step(model, true, roll);
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishInLine);
    assert(model.current_fish_number() == expected_fish_number);
}

void catch_boot(fh::FishingModel& model)
{
    hook_boot(model);
    int guard = 1000;
    int phase = 0;
    while(model.state() == fh::FishingState::FishInLine && --guard)
    {
        // Refill the tension meter periodically while still making net progress.
        const bool held = phase < 80;
        step(model, held, 0);
        phase = (phase + 1) % 120;
    }
    assert(guard > 0);
    assert(model.state() == fh::FishingState::FishCatch);
}

}

int main()
{
    static_assert(int(fh::FishingState::Init) == 0);
    static_assert(int(fh::FishingState::Stand) == 1);
    static_assert(int(fh::FishingState::Recoil) == 2);
    static_assert(int(fh::FishingState::GetReadyToThrow) == 3);
    static_assert(int(fh::FishingState::Throw) == 4);
    static_assert(int(fh::FishingState::BaitInWater) == 5);
    static_assert(int(fh::FishingState::FishInLine) == 6);
    static_assert(int(fh::FishingState::LineBreak) == 7);
    static_assert(int(fh::FishingState::FishCatch) == 8);
    static_assert(int(fh::FishingState::Reward) == 9);

    {
        fh::FishingModel crystal(1, 0, 0);
        fh::FishingModel pier(2, 1, 0);
        fh::FishingModel river(3, 2, 0);
        fh::FishingModel invalid(99, 0, 0);
        assert(crystal.pool() == 1);
        assert(pier.pool() == 2);
        assert(river.pool() == 3);
        assert(invalid.pool() == 1);
        assert(crystal.stick_strength() == 10);
        assert(pier.stick_strength() == 12);
        assert(river.stick_strength() == 14);
    }

    {
        fh::FishingModel pier(2, 0, 0);
        hook_movement_two(pier, 1, 4); // CAN
    }

    {
        fh::FishingModel river(3, 0, 0);
        hook_movement_one(river, 4, 30); // NOTTODAY
    }

    {
        fh::FishingModel ocean(4, 0, 0);
        hook_movement_two(ocean, 1, 5); // PLASTIC BAG
    }

    {
        fh::FishingModel cave(5, 0, 0);
        hook_movement_one(cave, 2, 21); // ILL-EEL
    }

    {
        fh::FishingModel model(1, 0, 0);
        assert(model.state() == fh::FishingState::Init);
        assert(model.sea_tile() == 112);
        assert(model.meter_x() == 37);
        assert(std::abs(model.line_distance() - 50.0f) < 0.001f);
        assert(model.stick_strength() == 10);
        assert(model.equipped_bait() == 0);
        model.set_equipped_bait(5);
        assert(model.equipped_bait() == 5);
        assert(model.bait_sprite() == 90);
        model.set_equipped_bait(99);
        assert(model.equipped_bait() == 5);
        model.set_equipped_bait(0);
        assert(model.equipped_bait() == 0);
        advance_to_stand(model);
        assert(model.ticks() == 0);
        assert(model.sea_tile() == 113);
        for(int frame = 2; frame <= 49; ++frame)
        {
            step(model);
            if(frame == 13) assert(model.sea_tile() == 114);
            if(frame == 25) assert(model.sea_tile() == 113);
            if(frame == 37) assert(model.sea_tile() == 112);
            if(frame == 49) assert(model.sea_tile() == 112);
        }
        step(model);
        assert(model.sea_tile() == 113);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 0);
        for(int index = 0; index < 10; ++index)
        {
            step(model);
        }
        assert(model.throw_delay() == 0);
        while(model.state() == fh::FishingState::Throw)
        {
            step(model);
        }
        assert(std::abs(model.line_distance() - 100.0f) < 0.001f);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 13); // 37 + 26 -> middle bucket.
        for(int index = 0; index < 10; ++index)
        {
            step(model);
        }
        assert(model.throw_delay() == 6);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 37); // max 111 -> high bucket.
        for(int index = 0; index < 10; ++index)
        {
            step(model);
        }
        assert(model.throw_delay() == 12);
        advance_to_bait(model);
        assert(std::abs(model.line_distance() - 248.0f) < 0.001f);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 37);
        advance_to_bait(model);
        assert(model.needs_random_roll());
        step(model, false, 7);
        assert(! model.needs_random_roll());
        assert(model.bait_move_points() == 0);
        assert(model.bait_movement_type() == 0);
        for(int index = 0; index < 13; ++index)
        {
            step(model, true, 0);
        }
        assert(model.bait_move_points() == 1);
        assert(model.bait_movement_type() == 1);
        for(int index = 0; index < 108; ++index)
        {
            step(model, true, 0);
        }
        assert(model.bait_move_points() == 10);
        assert(model.bait_movement_type() == 2);
        for(int index = 0; index < 24; ++index)
        {
            step(model, false, 0);
        }
        assert(model.bait_move_points() == 9);
        assert(model.bait_movement_type() == 1);
    }

    {
        // Roll zero is intentionally empty in Crystal Lake even when all lure
        // conditions match BOOT.
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 37);
        advance_to_bait(model, 0);
        for(int index = 0; index < 180; ++index)
        {
            step(model, true, 0);
        }
        assert(model.state() != fh::FishingState::FishInLine);
        assert(model.current_fish_number() == 0);
    }

    {
        // BOOT is wildcard bait but requires movement class 2 and 10
        // consecutive qualified lure checks.
        fh::FishingModel model(1, 0, 0);
        hook_boot(model);
        assert(model.current_fish_number() == 3);
        assert(model.current_fish_strength() == 4);
        step(model, true, 0);
        step(model, true, 0);
        assert(model.current_stamina() == 0);
        assert(model.current_fish_strength() == 1);
    }

    {
        // UNICUDA remains strong long enough for the original tension meter to
        // hit its lower bound while the player keeps holding the rod.
        fh::FishingModel model(1, 0, 5);
        hook_unicuda(model);
        int guard = 220;
        while(model.state() == fh::FishingState::FishInLine && --guard)
        {
            step(model, true, 0);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::LineBreak);
        assert(model.meter_x() <= 37);
    }

    {
        // Releasing against UNICUDA lets the line exceed 280 and breaks it.
        fh::FishingModel model(1, 0, 5);
        hook_unicuda(model);
        int guard = 160;
        while(model.state() == fh::FishingState::FishInLine && --guard)
        {
            step(model, false, 0);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::LineBreak);
        assert(model.line_distance() > 280.0f);

        while(model.state() == fh::FishingState::LineBreak && ! model.dialog_alive())
        {
            step(model);
        }
        assert(model.dialog_kind() == fh::FishingDialog::LineBreak);
        step(model, false, 0, true);
        assert(model.state() == fh::FishingState::Init);
    }

    {
        fh::FishingModel model(1, 0, 0);
        catch_boot(model);
        assert(model.line_distance() <= 48.0f);
        while(model.state() == fh::FishingState::FishCatch && ! model.dialog_alive())
        {
            step(model);
        }
        assert(model.dialog_kind() == fh::FishingDialog::Catch);
        assert(model.dialog_fish_name() != nullptr);
        step(model, false, 0, true);
        assert(model.state() == fh::FishingState::Reward);

        fh::FishingReward reward;
        int guard = 80;
        while(! reward.valid && --guard)
        {
            step(model);
            reward = model.take_reward();
        }
        assert(guard > 0);
        assert(reward.valid);
        assert(reward.fish_number == 3);
        assert(reward.amount == 1);
        assert(! model.take_reward().valid);
    }

    {
        // Reeling an empty cast all the way back enters recoil and eventually
        // returns through INIT.
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 10);
        advance_to_bait(model, 0);
        int guard = 600;
        while(model.state() == fh::FishingState::BaitInWater && --guard)
        {
            step(model, true, 0);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::Recoil);
        while(model.state() == fh::FishingState::Recoil && --guard)
        {
            step(model);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::Init);
    }


    {
        fh::FishingModel model(1, 0, 0);
        assert(model.take_sound_event() == fh::FishingSoundEvent::None);
        model.set_equipped_bait(5);
        assert(model.take_sound_event() == fh::FishingSoundEvent::NextPage);
        assert(model.take_sound_event() == fh::FishingSoundEvent::None);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 0);
        bool heard_throw = false;
        bool heard_water = false;
        int guard = 100;
        while(model.state() == fh::FishingState::Throw && --guard)
        {
            step(model);
            const fh::FishingSoundEvent event = model.take_sound_event();
            heard_throw |= event == fh::FishingSoundEvent::Throw;
            heard_water |= event == fh::FishingSoundEvent::Water;
        }
        assert(guard > 0);
        assert(heard_throw);
        assert(heard_water);
    }

    {
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 37);
        advance_to_bait(model, 1);
        drain_sounds(model);
        bool heard_hook = false;
        int guard = 240;
        while(model.state() == fh::FishingState::BaitInWater && --guard)
        {
            step(model, true, 1);
            fh::FishingSoundEvent event = model.take_sound_event();
            heard_hook |= event == fh::FishingSoundEvent::FishCatchBait;
        }
        assert(guard > 0);
        assert(heard_hook);
    }

    {
        fh::FishingModel model(1, 0, 5);
        hook_unicuda(model);
        drain_sounds(model);
        while(model.state() == fh::FishingState::FishInLine)
        {
            step(model, true, 0);
            (void) model.take_sound_event();
        }
        assert(model.state() == fh::FishingState::LineBreak);
        step(model);
        assert(model.take_sound_event() == fh::FishingSoundEvent::LineBreak);
    }

    {
        fh::FishingModel model(1, 0, 0);
        catch_boot(model);
        drain_sounds(model);
        step(model);
        assert(model.take_sound_event() == fh::FishingSoundEvent::Water);

        bool heard_fanfare = false;
        while(model.state() == fh::FishingState::FishCatch && ! model.dialog_alive())
        {
            step(model);
            heard_fanfare |= model.take_sound_event() == fh::FishingSoundEvent::Fanfare;
        }
        assert(heard_fanfare);
        step(model, false, 0, true);
        assert(model.state() == fh::FishingState::Reward);

        bool heard_coin = false;
        int guard = 30;
        while(! heard_coin && --guard)
        {
            step(model);
            heard_coin |= model.take_sound_event() == fh::FishingSoundEvent::Coin;
        }
        assert(heard_coin);
    }

    {
        // SELECT cancels an unhooked cast through Recoil so A can cast again.
        fh::FishingModel model(1, 0, 0);
        cast_with_charge_frames(model, 20);
        advance_to_bait(model, 0);
        assert(model.state() == fh::FishingState::BaitInWater);
        step(model, false, 0, false, true);
        assert(model.state() == fh::FishingState::Recoil);
        int guard = 120;
        while(model.state() != fh::FishingState::Stand && --guard)
        {
            step(model);
        }
        assert(guard > 0);
        assert(model.state() == fh::FishingState::Stand);
    }

    return 0;
}
