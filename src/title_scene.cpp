#include "title_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_title.h"

#include "flow_model.h"

namespace fh
{

TitleScene::TitleScene() :
    _background(bn::regular_bg_items::title.create_bg(0, 0))
{
}

void TitleScene::update(FlowModel& flow)
{
    if(bn::keypad::a_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_title_command(TitleCommand::Play);
    }
    else if(bn::keypad::start_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_title_command(TitleCommand::Options);
    }

    if(flow.state() != GameState::Title)
    {
        return;
    }

    // Keep the recovered title timing alive while native ROM bring-up uses
    // the single-map title background. The animated multi-map background is
    // intentionally not touched here until its runtime path is proven safe.
    flow.update_title_animation();
}



AudioCue TitleScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
