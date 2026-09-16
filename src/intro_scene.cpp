#include "intro_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_intro_credit_bg.h"

#include "flow_model.h"

namespace fh
{

IntroScene::IntroScene() :
    _background(bn::regular_bg_items::intro_credit_bg.create_bg(0, 0))
{
}

void IntroScene::update(FlowModel& flow)
{
    if(bn::keypad::select_pressed())
    {
        _model.skip(flow);
        return;
    }

    const IntroEvent event = _model.update();
    if(event == IntroEvent::FadeInAndSound)
    {
        _audio_event = AudioCue::Intro;
        _presentation_event = event;
    }
    else if(event == IntroEvent::FadeOut)
    {
        _presentation_event = event;
    }
    else if(event == IntroEvent::Complete)
    {
        _model.complete(flow);
    }
}

AudioCue IntroScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

IntroEvent IntroScene::take_presentation_event() noexcept
{
    const IntroEvent result = _presentation_event;
    _presentation_event = IntroEvent::None;
    return result;
}

}
