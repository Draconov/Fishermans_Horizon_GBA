#ifndef FH_INTRO_SCENE_H
#define FH_INTRO_SCENE_H

#include "bn_regular_bg_ptr.h"

#include "audio_cue.h"
#include "intro_model.h"

namespace fh
{

class FlowModel;

class IntroScene
{
public:
    IntroScene();
    void update(FlowModel& flow);
    [[nodiscard]] AudioCue take_audio_event() noexcept;
    [[nodiscard]] IntroEvent take_presentation_event() noexcept;

private:
    IntroModel _model;
    bn::regular_bg_ptr _background;
    AudioCue _audio_event = AudioCue::None;
    IntroEvent _presentation_event = IntroEvent::None;
};

}

#endif
