#ifndef FH_TITLE_SCENE_H
#define FH_TITLE_SCENE_H

#include "bn_regular_bg_ptr.h"

#include "audio_cue.h"

namespace fh
{

class FlowModel;

class TitleScene
{
public:
    TitleScene();

    void update(FlowModel& flow);
    [[nodiscard]] AudioCue take_audio_event() noexcept;

private:
    bn::regular_bg_ptr _background;
    int _sea_tile = 112;
    AudioCue _audio_event = AudioCue::None;
};

}

#endif
