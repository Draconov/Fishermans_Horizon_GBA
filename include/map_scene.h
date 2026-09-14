#ifndef FH_MAP_SCENE_H
#define FH_MAP_SCENE_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "audio_cue.h"
#include "flow_model.h"

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
    void _update_marker_visibility(const FlowModel& flow);
    void _update_character(const FlowModel& flow);
    void _update_selection(const FlowModel& flow);
    void _update_catalog(const FlowModel& flow);
    void _update_text(const FlowModel& flow);

    bn::regular_bg_ptr _background;
    bn::sprite_ptr _shop_spot;
    bn::sprite_ptr _crystal_spot;
    bn::sprite_ptr _pier_spot;
    bn::sprite_ptr _river_spot;
    bn::sprite_ptr _ocean_spot;
    bn::sprite_ptr _cave_spot;
    bn::sprite_ptr _character;
    bn::sprite_ptr _selection_cursor;
    bn::vector<bn::sprite_ptr, 3> _catalog_parts;
    bn::vector<bn::sprite_ptr, 24> _text_sprites;
    int _spot_a_graphics_index = 0;
    int _spot_b_graphics_index = 2;
    int _last_character = -1;
    MapTarget _last_target = MapTarget::CrystalLake;
    bool _has_last_target = false;
    bool _text_dirty = true;
    AudioCue _audio_event = AudioCue::None;
};

}

#endif
