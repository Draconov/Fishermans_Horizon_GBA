#ifndef FH_FISHING_SCENE_H
#define FH_FISHING_SCENE_H

#include "bn_random.h"
#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "fishing_model.h"
#include "dialog_model.h"
#include "dialog_renderer.h"

#include "audio_cue.h"

namespace fh
{

class FlowModel;

class FishingScene
{
public:
    FishingScene(int pool, int rod_index, int equipped_bait, int character_index);

    void update(FlowModel& flow);
    [[nodiscard]] AudioCue take_audio_event() noexcept;
    [[nodiscard]] bool take_flash_request() noexcept;

private:
    void _render();
    void _render_hud_text(const FlowModel& flow);
    void _render_bait_or_fish();
    void _render_line();
    void _start_result_dialog();

    int _pool;
    int _character_index;
    FishingModel _model;
    bn::random _random;
    bn::regular_bg_ptr _background;
    bn::sprite_ptr _character;
    bn::sprite_ptr _rod_left;
    bn::sprite_ptr _rod_right_top;
    bn::sprite_ptr _rod_right_bottom;
    bn::sprite_ptr _bait;
    bn::sprite_ptr _fish_bank0;
    bn::sprite_ptr _fish_bank1;
    bn::sprite_ptr _splash;
    bn::sprite_ptr _coin;
    bn::sprite_ptr _back_icon;
    bn::sprite_ptr _bait_icon;
    bn::sprite_ptr _meter;
    bn::vector<bn::sprite_ptr, 16> _hud_text_sprites;
    bn::vector<bn::sprite_ptr, 32> _line_dots;
    int _background_map_index = -1;
    int _last_hud_bait = -1;
    int _last_hud_money = -1;
    bool _last_hud_dialog_active = false;
    AudioCue _audio_event = AudioCue::None;
    DialogModel _dialog;
    DialogRenderer _dialog_renderer;
    char _dialog_text[96]{};
    bool _flash_request = false;
};

}

#endif
