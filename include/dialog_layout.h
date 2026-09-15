#ifndef FH_DIALOG_LAYOUT_H
#define FH_DIALOG_LAYOUT_H

#include "m4_text_layout.h"

namespace fh
{

[[nodiscard]] constexpr int dialog_character_x_adjust(char character) noexcept
{
    return m4_character_x_adjust(character);
}

[[nodiscard]] constexpr int dialog_character_advance(char character) noexcept
{
    return m4_character_advance(character);
}

[[nodiscard]] constexpr int dialog_character_draw_x_adjust(char character) noexcept
{
    return m4_character_draw_x_adjust(character);
}

[[nodiscard]] constexpr bool dialog_character_visible(char character) noexcept
{
    return character != ' ' && character != '#' && character != '@';
}

inline void dialog_consume_character(char character, int& x, int& y) noexcept
{
    if(character == ' ')
    {
        if(x == 8)
        {
            x = 1;
        }
        else if(x > 180)
        {
            y += 9;
            x = 1;
        }
    }
    else if(character == '#')
    {
        y += 9;
        x = 1;
    }
    else if(character == '@')
    {
        y += 18;
        x = 1;
    }
    else
    {
        x += dialog_character_advance(character);
        return;
    }

    // DialogBox.drawDialog always adds seven after getChar() for layout
    // controls such as spaces and the #/@ line controls.
    x += 7;
}

inline void dialog_apply_line_cutoff(int& x, int& y) noexcept
{
    if(x >= 210 && y < 22)
    {
        y += 9;
        x = 8;
    }
}

}

#endif
