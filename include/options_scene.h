#ifndef FH_OPTIONS_SCENE_H
#define FH_OPTIONS_SCENE_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "options_model.h"

#include "audio_cue.h"

namespace fh
{

class FlowModel;

class OptionsScene
{
public:
    OptionsScene();
    void update(FlowModel& flow);
    [[nodiscard]] AudioCue take_audio_event() noexcept;

private:
    void _advance_background();
    void _render(const FlowModel& flow);

    OptionsModel _model;
    bn::regular_bg_ptr _background;
    bn::sprite_ptr _cursor;
    bn::vector<bn::sprite_ptr, 32> _text_sprites;
    int _sea_ticks = 0;
    int _map_index = 0;
    AudioCue _audio_event = AudioCue::None;
};

}

#endif
