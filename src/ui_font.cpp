#include "ui_font.h"

namespace fh
{

int ui_font_glyph(char character) noexcept
{
    if(character >= '0' && character <= '9')
    {
        return character - '0';
    }
    if(character >= 'a' && character <= 'z')
    {
        return 16 + (character - 'a') * 2;
    }
    if(character >= 'A' && character <= 'Z')
    {
        return 17 + (character - 'A') * 2;
    }

    switch(character)
    {
    case '.': return 68;
    case ',': return 69;
    case '!': return 70;
    case '?': return 71;
    case ':': return 72;
    case '<': return 73; // The original strings use '<' for the apostrophe glyph.
    case '-': return 74;
    default: return -1;
    }
}

}
