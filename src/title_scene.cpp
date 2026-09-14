#include "title_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_title_anim.h"

#include "flow_model.h"

namespace fh
{

TitleScene::TitleScene() :
    _background(bn::regular_bg_items::title_anim.create_bg(0, 0, 0))
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

    flow.update_title_animation();
    const int next_map_index = flow.title_sea_tile() - 112;
    if(next_map_index != _map_index)
    {
        _map_index = next_map_index;
        _background.set_map(bn::regular_bg_items::title_anim.map_item(), _map_index);
    }
}



AudioCue TitleScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
