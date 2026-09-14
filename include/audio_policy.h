#ifndef FH_AUDIO_POLICY_H
#define FH_AUDIO_POLICY_H

#include "audio_cue.h"
#include "fishing_model.h"
#include "game_state.h"

namespace fh
{

enum class SceneTrack
{
    None,
    Title,
    MariMari,
    Select,
    Welcome,
    Inherit,
};

[[nodiscard]] SceneTrack scene_track(GameState state) noexcept;
[[nodiscard]] int scene_track_loop_frames(SceneTrack track) noexcept;
[[nodiscard]] AudioCue audio_cue_from_fishing(FishingSoundEvent event) noexcept;

}

#endif
