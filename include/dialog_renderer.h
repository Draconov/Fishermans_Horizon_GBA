#ifndef FH_DIALOG_RENDERER_H
#define FH_DIALOG_RENDERER_H

#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "dialog_model.h"

namespace fh
{

class DialogRenderer
{
public:
    DialogRenderer();

    void render(const DialogModel& dialog);
    void hide();

private:
    void _set_panel_y(int box_y);
    void _rebuild_text(const DialogModel& dialog);

    bn::sprite_ptr _panel0;
    bn::sprite_ptr _panel1;
    bn::sprite_ptr _panel2;
    bn::sprite_ptr _panel3;
    bn::sprite_ptr _marker_base;
    bn::sprite_ptr _marker_advance;
    bn::vector<bn::sprite_ptr, 64> _text_sprites;
    int _last_box_y = -1;
    int _last_page_start = -1;
    int _last_visible_end = -1;
    bool _last_waiting = false;
};

}

#endif
