#ifndef FH_MAP_SCENE_H
#define FH_MAP_SCENE_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"

#include "audio_cue.h"

namespace fh
{

class FlowModel;

class MapScene
{
public:
    MapScene();

    void update(FlowModel& flow);
    [[nodiscard]] AudioCue take_audio_event() noexcept;

private:
    void _update_marker_graphics(const FlowModel& flow);
    void _update_selection_visibility(const FlowModel& flow);

    bn::regular_bg_ptr _background;
    bn::sprite_ptr _shop_spot;
    bn::sprite_ptr _crystal_spot;
    bn::sprite_ptr _pier_spot;
    bn::sprite_ptr _river_spot;
    bn::sprite_ptr _ocean_spot;
    bn::sprite_ptr _cave_spot;
    int _spot_a_graphics_index = 0;
    int _spot_b_graphics_index = 2;
    int _selection_ticks = 0;
    AudioCue _audio_event = AudioCue::None;
};

}

#endif
