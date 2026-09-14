#include <cassert>

#include "audio_policy.h"

int main()
{
    using fh::AudioCue;
    using fh::SceneTrack;

    assert(fh::scene_track(fh::GameState::Title) == SceneTrack::Title);
    assert(fh::scene_track(fh::GameState::Map) == SceneTrack::MariMari);
    assert(fh::scene_track(fh::GameState::Shop) == SceneTrack::Select);
    assert(fh::scene_track(fh::GameState::Catalog) == SceneTrack::Select);
    assert(fh::scene_track(fh::GameState::Event) == SceneTrack::Welcome);
    assert(fh::scene_track(fh::GameState::Fishing) == SceneTrack::Inherit);
    assert(fh::scene_track(fh::GameState::Options) == SceneTrack::Title);
    assert(fh::scene_track(fh::GameState::Intro) == SceneTrack::None);

    assert(fh::scene_track_loop_frames(SceneTrack::Title) == 2472);
    assert(fh::scene_track_loop_frames(SceneTrack::MariMari) == 209);
    assert(fh::scene_track_loop_frames(SceneTrack::Select) == 209);
    assert(fh::scene_track_loop_frames(SceneTrack::Welcome) == 414);
    assert(fh::scene_track_loop_frames(SceneTrack::None) == 0);
    assert(fh::scene_track_loop_frames(SceneTrack::Inherit) == 0);

    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::None) == AudioCue::None);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::NextPage) == AudioCue::NextPage);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Throw) == AudioCue::Throw);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::LineBreak) == AudioCue::LineBreak);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Coin) == AudioCue::Coin);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::FishCatchBait) == AudioCue::FishCatchBait);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Water) == AudioCue::Water);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Fanfare) == AudioCue::Fanfare);
    assert(fh::audio_cue_from_fishing(fh::FishingSoundEvent::Coil) == AudioCue::Coil);
    return 0;
}
