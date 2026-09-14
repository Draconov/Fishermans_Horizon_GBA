#ifndef FH_SHOP_SCENE_H
#define FH_SHOP_SCENE_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "shop_model.h"

#include "audio_cue.h"

namespace fh
{

class FlowModel;

class ShopScene
{
public:
    ShopScene();
    void update(FlowModel& flow);
    [[nodiscard]] AudioCue take_audio_event() noexcept;

private:
    void _render(FlowModel& flow);

    ShopModel _model;
    bn::regular_bg_ptr _background;
    bn::sprite_ptr _keeper;
    bn::sprite_ptr _cursor;
    bn::vector<bn::sprite_ptr, 16> _sold_out_sprites;
    bn::vector<bn::sprite_ptr, 64> _text_sprites;
    ShopPurchaseResult _last_result = ShopPurchaseResult::InvalidItem;
    int _keeper_ticks = 0;
    int _keeper_frame = 0;
    bool _dirty = true;
    AudioCue _audio_event = AudioCue::None;
};

}

#endif
