#include "event_scene.h"

#include "bn_keypad.h"
#include "bn_regular_bg_items_m4_event_anim.h"
#include "bn_sprite_items_m4_event_cecil.h"

#include "event_model.h"
#include "flow_model.h"

namespace fh
{
namespace
{

constexpr int EVENT_DIALOG_OPEN_TICK = 100;

}

EventScene::EventScene(int event_id) :
    _model(event_id),
    _background(bn::regular_bg_items::m4_event_anim.create_bg(0, 0, 0)),
    _cecil(bn::sprite_items::m4_event_cecil.create_sprite(-84, 24, 0))
{
}

void EventScene::update(FlowModel& flow)
{
    ++_event_ticks;
    if(! _begun && _event_ticks == EVENT_DIALOG_OPEN_TICK)
    {
        _begun = true;
        _model.begin(flow);
        _dialog.start(_model.text());
    }

    if(_begun)
    {
        const DialogEvent event = _dialog.update(bn::keypad::a_pressed());
        if(event == DialogEvent::NextPage)
        {
            _audio_event = AudioCue::NextPage;
        }
        _dialog_renderer.render(_dialog);
        if(event == DialogEvent::Closed)
        {
            _model.complete(flow);
            return;
        }
    }

    if(_dialog.talking())
    {
        ++_cecil_ticks;
        if(_cecil_ticks % 8 == 0)
        {
            if(_cecil_frame != 0)
            {
                _cecil_frame = 0;
                _cecil.set_tiles(bn::sprite_items::m4_event_cecil.tiles_item(), 0);
            }
            _cecil_ticks = 0;
        }
        else if(_cecil_ticks % 4 == 0 && _cecil_frame != 1)
        {
            _cecil_frame = 1;
            _cecil.set_tiles(bn::sprite_items::m4_event_cecil.tiles_item(), 1);
        }
    }
    else if(_cecil_ticks > 0)
    {
        ++_cecil_ticks;
        if(_cecil_ticks % 12 == 0)
        {
            if(_cecil_frame != 0)
            {
                _cecil_frame = 0;
                _cecil.set_tiles(bn::sprite_items::m4_event_cecil.tiles_item(), 0);
            }
            _cecil_ticks = 0;
        }
    }
    _advance_background();
}

void EventScene::_advance_background()
{
    ++_sea_ticks;
    int next_map = _map_index;
    if(_sea_ticks == 1) next_map = 1;
    else if(_sea_ticks == 13) next_map = 2;
    else if(_sea_ticks == 25) next_map = 1;
    else if(_sea_ticks == 37) next_map = 0;
    else if(_sea_ticks == 49) _sea_ticks = 0;
    if(next_map != _map_index)
    {
        _map_index = next_map;
        _background.set_map(bn::regular_bg_items::m4_event_anim.map_item(), _map_index);
    }
}

AudioCue EventScene::take_audio_event() noexcept
{
    const AudioCue result = _audio_event;
    _audio_event = AudioCue::None;
    return result;
}

}
