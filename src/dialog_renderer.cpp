#include "dialog_renderer.h"

#include "bn_sprite_items_m4_font.h"
#include "bn_sprite_items_m7_dialog_dollar.h"
#include "bn_sprite_items_m7_dialog_markers.h"
#include "bn_sprite_items_m7_dialog_panel.h"

#include "dialog_layout.h"
#include "m4_font.h"

namespace fh
{

DialogRenderer::DialogRenderer() :
    _panel0(bn::sprite_items::m7_dialog_panel.create_sprite(-88, 96, 0)),
    _panel1(bn::sprite_items::m7_dialog_panel.create_sprite(-24, 96, 0)),
    _panel2(bn::sprite_items::m7_dialog_panel.create_sprite(40, 96, 0)),
    _panel3(bn::sprite_items::m7_dialog_panel.create_sprite(104, 96, 1)),
    _marker_base(bn::sprite_items::m7_dialog_markers.create_sprite(108, 92, 0)),
    _marker_advance(bn::sprite_items::m7_dialog_markers.create_sprite(108, 92, 1))
{
    hide();
}

void DialogRenderer::render(const DialogModel& dialog)
{
    if(! dialog.active() && dialog.done())
    {
        hide();
        return;
    }

    const int box_y = dialog.box_y();
    const bool panel_visible = box_y < 160;
    _panel0.set_visible(panel_visible);
    _panel1.set_visible(panel_visible);
    _panel2.set_visible(panel_visible);
    _panel3.set_visible(panel_visible);
    _marker_base.set_visible(panel_visible);
    _marker_advance.set_visible(panel_visible && dialog.waiting_for_advance());

    if(box_y != _last_box_y)
    {
        _set_panel_y(box_y);
        _last_box_y = box_y;
    }

    if(dialog.page_start() != _last_page_start || dialog.visible_end() != _last_visible_end ||
       dialog.waiting_for_advance() != _last_waiting || box_y != 136)
    {
        _rebuild_text(dialog);
        _last_page_start = dialog.page_start();
        _last_visible_end = dialog.visible_end();
        _last_waiting = dialog.waiting_for_advance();
    }
}

void DialogRenderer::hide()
{
    _panel0.set_visible(false);
    _panel1.set_visible(false);
    _panel2.set_visible(false);
    _panel3.set_visible(false);
    _marker_base.set_visible(false);
    _marker_advance.set_visible(false);
    _text_sprites.clear();
    _last_box_y = -1;
    _last_page_start = -1;
    _last_visible_end = -1;
    _last_waiting = false;
}

void DialogRenderer::_set_panel_y(int box_y)
{
    const int panel_y = box_y - 64;
    _panel0.set_y(panel_y);
    _panel1.set_y(panel_y);
    _panel2.set_y(panel_y);
    _panel3.set_y(panel_y);
    const int marker_y = box_y - 68;
    _marker_base.set_y(marker_y);
    _marker_advance.set_y(marker_y);
}

void DialogRenderer::_rebuild_text(const DialogModel& dialog)
{
    _text_sprites.clear();
    if(dialog.visible_end() <= dialog.page_start())
    {
        return;
    }

    int x = 8;
    int y = 4;
    const char* text = dialog.text();
    const int box_y = dialog.box_y();

    for(int index = dialog.page_start(); index < dialog.visible_end(); ++index)
    {
        const char character = text[index];
        if(dialog_character_visible(character))
        {
            if(character == '$')
            {
                _text_sprites.push_back(bn::sprite_items::m7_dialog_dollar.create_sprite(
                    x + 1 + 4 - 120, box_y + y + 4 - 80, 0));
            }
            else
            {
                const int glyph = m4_font_glyph(character);
                if(glyph >= 0)
                {
                    _text_sprites.push_back(bn::sprite_items::m4_font.create_sprite(
                        x + 4 - 120, box_y + y + 4 - 80, glyph));
                }
            }
        }

        dialog_consume_character(character, x, y);

        if(x >= 210 && y < 22)
        {
            const char next = text[index + 1];
            if(next && next != ' ' && next != '#' && next != '@')
            {
                const int hyphen = m4_font_glyph('-');
                _text_sprites.push_back(bn::sprite_items::m4_font.create_sprite(
                    x + 4 - 120, box_y + y + 4 - 80, hyphen));
            }
            dialog_apply_line_cutoff(x, y);
        }
    }
}

}
