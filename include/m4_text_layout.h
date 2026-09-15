#ifndef FH_M4_TEXT_LAYOUT_H
#define FH_M4_TEXT_LAYOUT_H

namespace fh
{

[[nodiscard]] constexpr int m4_character_x_adjust(char character) noexcept
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

[[nodiscard]] constexpr int m4_character_advance(char character) noexcept
{
    return 7 + m4_character_x_adjust(character);
}

[[nodiscard]] constexpr int m4_character_draw_x_adjust(char character) noexcept
{
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

[[nodiscard]] inline int m4_text_width(const char* text, int max_chars) noexcept
{
    int width = 0;
    int count = 0;
    while(text && *text && count < max_chars)
    {
        const char character = *text++;
        if(character == '#')
        {
            break;
        }
        width += m4_character_advance(character);
        ++count;
    }
    return width;
}

}

#endif
