#ifndef FH_CATALOG_SCENE_H
#define FH_CATALOG_SCENE_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "catalog_model.h"

#include "audio_cue.h"

namespace fh
{

class FlowModel;

class CatalogScene
{
public:
    CatalogScene();
    void update(FlowModel& flow);
    [[nodiscard]] AudioCue take_audio_event() noexcept;

private:
    void _advance_background();
    void _build_fish_grid(const FlowModel& flow);
    void _render_text(const FlowModel& flow);
    void _update_cursor();

    CatalogModel _model;
    bn::regular_bg_ptr _background;
    bn::sprite_ptr _cursor;
    bn::vector<bn::sprite_ptr, 44> _fish_sprites;
    bn::vector<bn::sprite_ptr, 64> _text_sprites;
    int _sea_ticks = 0;
    int _map_index = 0;
    bool _grid_built = false;
    AudioCue _audio_event = AudioCue::None;
};

}

#endif
