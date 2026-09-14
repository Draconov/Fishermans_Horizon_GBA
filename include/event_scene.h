#ifndef FH_EVENT_SCENE_H
#define FH_EVENT_SCENE_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"

#include "audio_cue.h"
#include "dialog_model.h"
#include "dialog_renderer.h"
#include "event_model.h"

namespace fh
{

class FlowModel;

class EventScene
{
public:
    explicit EventScene(int event_id);
    void update(FlowModel& flow);
    [[nodiscard]] AudioCue take_audio_event() noexcept;

private:
    void _advance_background();

    EventModel _model;
    DialogModel _dialog;
    DialogRenderer _dialog_renderer;
    bn::regular_bg_ptr _background;
    bn::sprite_ptr _cecil;
    int _event_ticks = 0;
    int _sea_ticks = 0;
    int _map_index = 0;
    int _cecil_ticks = 0;
    int _cecil_frame = 0;
    bool _begun = false;
    AudioCue _audio_event = AudioCue::None;
};

}

#endif
