#ifndef FH_SHOP_SCENE_H
#define FH_SHOP_SCENE_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "audio_cue.h"
#include "dialog_model.h"
#include "dialog_renderer.h"
#include "shop_model.h"

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
    void _start_description(const FlowModel& flow);
    void _update_keeper_animation();
    void _set_keeper_frame(int frame);
    void _render(FlowModel& flow);

    ShopModel _model;
    DialogModel _dialog;
    DialogRenderer _dialog_renderer;
    bn::regular_bg_ptr _background;
    bn::sprite_ptr _keeper;
    bn::sprite_ptr _cursor;
    bn::sprite_ptr _locked_overlay;
    bn::sprite_ptr _buy_enabled;
    bn::vector<bn::sprite_ptr, 16> _sold_out_sprites;
    bn::vector<bn::sprite_ptr, 20> _text_sprites;
    ShopPurchaseResult _last_result = ShopPurchaseResult::InvalidItem;
    int _keeper_ticks = 0;
    int _keeper_frame = 0;
    bool _needs_description = true;
    bool _dirty = true;
    AudioCue _audio_event = AudioCue::None;
};

}

#endif
