#ifndef FH_AUDIO_MANAGER_H
#define FH_AUDIO_MANAGER_H

#include "bn_optional.h"
#include "bn_sound_handle.h"

#include "audio_cue.h"
#include "audio_policy.h"
#include "game_state.h"

namespace fh
{

class AudioManager
{
public:
    void update(GameState state, int sound_option);
    void play(AudioCue cue, int sound_option);

private:
    void _start_track(SceneTrack track);
    void _stop_music();

    SceneTrack _track = SceneTrack::None;
    bn::optional<bn::sound_handle> _music_handle;
    int _music_frames = 0;
};

}

#endif
