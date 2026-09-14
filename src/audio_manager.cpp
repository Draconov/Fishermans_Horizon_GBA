#include "audio_manager.h"

#include "bn_music.h"
#include "bn_music_items.h"
#include "bn_sound_items.h"

namespace fh
{

void AudioManager::update(GameState state, int sound_option)
{
    const SceneTrack desired = scene_track(state);
    if(desired != SceneTrack::Inherit && desired != _track)
    {
        _stop_music();
        _track = desired;
        _music_frames = 0;
    }

    if(sound_option == 0)
    {
        _stop_music();
        return;
    }

    if(_track == SceneTrack::None || _track == SceneTrack::Inherit)
    {
        return;
    }

    if(_track == SceneTrack::Title)
    {
        if(! bn::music::playing())
        {
            _start_track(_track);
        }
        return;
    }

    const int loop_frames = scene_track_loop_frames(_track);
    if(! _music_handle || ! _music_handle->active() || (loop_frames > 0 && _music_frames >= loop_frames))
    {
        _start_track(_track);
    }
    else
    {
        ++_music_frames;
    }
}

void AudioManager::play(AudioCue cue, int sound_option)
{
    if(sound_option == 0 || cue == AudioCue::None)
    {
        return;
    }

    switch(cue)
    {
    case AudioCue::None: break;
    case AudioCue::NextPage: (void) bn::sound_items::next_page.play(); break;
    case AudioCue::Throw: (void) bn::sound_items::throw_sfx.play(); break;
    case AudioCue::LineBreak: (void) bn::sound_items::line_break.play(); break;
    case AudioCue::Coin: (void) bn::sound_items::coin.play(); break;
    case AudioCue::FishCatchBait: (void) bn::sound_items::fish_catch_bait.play(); break;
    case AudioCue::Water: (void) bn::sound_items::water.play(); break;
    case AudioCue::Fanfare: (void) bn::sound_items::fanfare.play(); break;
    case AudioCue::Coil: (void) bn::sound_items::coil.play(); break;
    case AudioCue::Intro: (void) bn::sound_items::intro.play(); break;
    }
}

void AudioManager::_start_track(SceneTrack track)
{
    _stop_music();
    switch(track)
    {
    case SceneTrack::Title: bn::music_items::title.play(1, true); break;
    case SceneTrack::MariMari: _music_handle = bn::sound_items::mari_mari.play(); break;
    case SceneTrack::Select: _music_handle = bn::sound_items::select.play(); break;
    case SceneTrack::Welcome: _music_handle = bn::sound_items::welcome.play(); break;
    case SceneTrack::None:
    case SceneTrack::Inherit:
        break;
    }
    _music_frames = 0;
}

void AudioManager::_stop_music()
{
    if(bn::music::playing())
    {
        bn::music::stop();
    }
    if(_music_handle && _music_handle->active())
    {
        _music_handle->stop();
    }
    _music_handle.reset();
    _music_frames = 0;
}

}
