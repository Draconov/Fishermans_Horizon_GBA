#include "audio_policy.h"

namespace fh
{

SceneTrack scene_track(GameState state) noexcept
{
    switch(state)
    {
    case GameState::Title: return SceneTrack::Title;
    case GameState::Map: return SceneTrack::MariMari;
    case GameState::Fishing: return SceneTrack::Inherit;
    case GameState::Shop: return SceneTrack::Select;
    case GameState::Catalog: return SceneTrack::Select;
    case GameState::Options: return SceneTrack::Title;
    case GameState::Event: return SceneTrack::Welcome;
    case GameState::Intro: return SceneTrack::None;
    }
    return SceneTrack::None;
}

int scene_track_loop_frames(SceneTrack track) noexcept
{
    switch(track)
    {
    case SceneTrack::Title: return 2472;
    case SceneTrack::MariMari: return 209;
    case SceneTrack::Select: return 209;
    case SceneTrack::Welcome: return 414;
    case SceneTrack::None:
    case SceneTrack::Inherit:
        return 0;
    }
    return 0;
}

AudioCue audio_cue_from_fishing(FishingSoundEvent event) noexcept
{
    switch(event)
    {
    case FishingSoundEvent::None: return AudioCue::None;
    case FishingSoundEvent::NextPage: return AudioCue::NextPage;
    case FishingSoundEvent::Throw: return AudioCue::Throw;
    case FishingSoundEvent::LineBreak: return AudioCue::LineBreak;
    case FishingSoundEvent::Coin: return AudioCue::Coin;
    case FishingSoundEvent::FishCatchBait: return AudioCue::FishCatchBait;
    case FishingSoundEvent::Water: return AudioCue::Water;
    case FishingSoundEvent::Fanfare: return AudioCue::Fanfare;
    case FishingSoundEvent::Coil: return AudioCue::Coil;
    }
    return AudioCue::None;
}

}
