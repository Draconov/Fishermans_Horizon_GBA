#include <cassert>
#include <cstring>

#include "dialog_model.h"

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

    return 0;
}
