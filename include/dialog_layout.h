#ifndef FH_DIALOG_LAYOUT_H
#define FH_DIALOG_LAYOUT_H

namespace fh
{

[[nodiscard]] constexpr int dialog_character_x_adjust(char character) noexcept
{
    switch(character)
    {
    case '1': return -2;
    case 'i': return -4;
    case 'I': return -2;
    case 'l': return -4;
    case 'p':
    case 'q':
    case 'Q': return 1;
    case 'm':
    case 'M':
    case 'w':
    case 'W': return 2;
    case '.': return -4;
    case ',': return -3;
    case '!': return -4;
    case ':': return -4;
    case '<': return -3;
    case '-': return -2;
    case '$': return 2;
    default: return 0;
    }
}

[[nodiscard]] constexpr int dialog_character_advance(char character) noexcept
{
    return 7 + dialog_character_x_adjust(character);
}

[[nodiscard]] constexpr int dialog_character_draw_x_adjust(char character) noexcept
{
    // These glyphs touch the left edge of their 8x8 source tile. Shifting
    // them one pixel right preserves the same one-empty-column visual gap
    // used by the rest of the proportional font.
    switch(character)
    {
    case 'm':
    case 'M':
    case 'w':
    case 'W':
    case 'p': return 1;
    default: return 0;
    }
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
