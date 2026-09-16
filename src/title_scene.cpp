#include "title_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_title_bg_0.h"
#include "bn_regular_bg_items_title_bg_1.h"
#include "bn_regular_bg_items_title_bg_2.h"

#include "flow_model.h"

namespace fh
{

TitleScene::TitleScene() :
    _background(bn::regular_bg_items::title_bg_0.create_bg(0, 0))
{
}

void TitleScene::update(FlowModel& flow)
{
    if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_title_command(TitleCommand::Play);
    }
    else if(bn::keypad::select_pressed())
    {
        _audio_event = AudioCue::NextPage;
        flow.handle_title_command(TitleCommand::Options);
    }

    if(flow.state() != GameState::Title)
    {
        return;
    }

    flow.update_title_animation();
    const int sea_tile = flow.title_sea_tile();
    if(sea_tile != _sea_tile)
    {
        _sea_tile = sea_tile;
        switch(sea_tile)
        {
        case 113:
            _background.set_item(bn::regular_bg_items::title_bg_1);
            break;
        case 114:
            _background.set_item(bn::regular_bg_items::title_bg_2);
            break;
        case 112:
        default:
            _background.set_item(bn::regular_bg_items::title_bg_0);
            break;
        }
    }
}



AudioCue TitleScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
