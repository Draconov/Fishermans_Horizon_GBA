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
    case 'm':
    case 'M':
    case 'w':
    case 'W': return 2;
    case '.': return -4;
    case ',': return -3;
    case '!': return -4;
    case '<': return -3;
    case '-': return -2;
    case '$': return 2;
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
        x += dialog_character_x_adjust(character);
    }

    // DialogBox.drawDialog always adds seven after getChar(), including
    // spaces and the #/@ layout controls.
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
