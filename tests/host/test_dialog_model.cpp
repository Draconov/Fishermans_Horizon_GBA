#include <cassert>
#include <cstring>

#include "dialog_model.h"
#include "dialog_layout.h"
#include "progression_content.h"

int main()
{
    {
        fh::DialogModel dialog("first#second##third");
        assert(dialog.box_y() == 160);
        assert(dialog.page_index() == 0);
        assert(! dialog.waiting_for_advance());
        assert(! dialog.done());

        // Original box slides from y=160 to y=136 by 2 pixels/update.
        for(int i = 0; i < 12; ++i)
        {
            assert(dialog.update(false) == fh::DialogEvent::None);
        }
        assert(dialog.box_y() == 136);
        assert(dialog.talking());

        // One source character is consumed per visible update. Two visible
        // lines fill the first page at the second '#'.
        while(! dialog.waiting_for_advance())
        {
            assert(dialog.update(false) == fh::DialogEvent::None);
        }
        assert(dialog.page_index() == 0);
        assert(dialog.visible_end() > dialog.page_start());
        assert(! dialog.talking());

        assert(dialog.update(true) == fh::DialogEvent::NextPage);
        assert(dialog.page_index() == 1);
        assert(! dialog.waiting_for_advance());

        while(! dialog.waiting_for_advance())
        {
            dialog.update(false);
        }
        assert(dialog.update(true) == fh::DialogEvent::NextPage);
        assert(! dialog.done());

        // Closing slides the box back down before becoming done.
        for(int i = 0; i < 11; ++i)
        {
            assert(dialog.update(false) == fh::DialogEvent::None);
            assert(! dialog.done());
        }
        assert(dialog.update(false) == fh::DialogEvent::Closed);
        assert(dialog.done());
        assert(dialog.box_y() == 160);
    }

    {
        // '#' advances one line and '@' advances a paragraph (two lines).
        fh::DialogModel dialog("A#B@C");
        for(int i = 0; i < 12; ++i) dialog.update(false);
        dialog.update(false); // A
        assert(dialog.cursor_x() == 15);
        assert(dialog.cursor_y() == 4);
        dialog.update(false); // #
        assert(dialog.cursor_x() == 8);
        assert(dialog.cursor_y() == 13);
        dialog.update(false); // B
        assert(dialog.cursor_x() == 15);
        dialog.update(false); // @
        assert(dialog.cursor_x() == 8);
        assert(dialog.cursor_y() == 31);
        assert(dialog.waiting_for_advance());
    }

    {
        // Leading spaces do not shift the original x=8 origin.
        fh::DialogModel dialog(" A");
        for(int i = 0; i < 12; ++i) dialog.update(false);
        dialog.update(false);
        assert(dialog.cursor_x() == 8);
        dialog.update(false);
        assert(dialog.cursor_x() == 15);
    }

    {
        fh::DialogModel dialog("temporary");
        assert(dialog.active());
        dialog.clear();
        assert(! dialog.active());
        assert(! dialog.talking());
        assert(! dialog.done());
    }

    {
        // Every Shop description must paginate through the shared DialogBox
        // without overflowing/stalling, including the longest character blurbs.
        for(int slot = 0; slot < fh::shop_item_count(); ++slot)
        {
            const fh::ShopItemSpec* item = fh::shop_item_spec(slot);
            assert(item);
            fh::DialogModel dialog(item->description);
            int guard = 0;
            while(! dialog.done() && guard < 1000)
            {
                const bool advance = dialog.waiting_for_advance();
                dialog.update(advance);
                assert(dialog.cursor_x() <= 210);
                ++guard;
            }
            assert(dialog.done());
            assert(guard < 1000);
        }
    }


    {
        // Dialog glyph placement keeps exactly one blank pixel between opaque
        // glyph bounds, including wide/edge-touching glyphs from m4_font.bmp.
        assert(fh::dialog_character_advance('A') == 7);
        assert(fh::dialog_character_advance('i') == 3);
        assert(fh::dialog_character_advance('m') == 9);
        assert(fh::dialog_character_advance('p') == 8);
        assert(fh::dialog_character_advance('q') == 8);
        assert(fh::dialog_character_advance('Q') == 8);
        assert(fh::dialog_character_advance(':') == 3);

        assert(fh::dialog_character_draw_x_adjust('A') == 0);
        assert(fh::dialog_character_draw_x_adjust('m') == 1);
        assert(fh::dialog_character_draw_x_adjust('w') == 1);
        assert(fh::dialog_character_draw_x_adjust('M') == 1);
        assert(fh::dialog_character_draw_x_adjust('W') == 1);
        assert(fh::dialog_character_draw_x_adjust('p') == 1);
        assert(fh::dialog_character_draw_x_adjust('q') == 0);
    }

    return 0;
}
