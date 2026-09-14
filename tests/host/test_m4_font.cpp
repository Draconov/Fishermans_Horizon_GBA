#include <cassert>
#include "m4_font.h"

int main()
{
    using fh::m4_font_glyph;
    assert(m4_font_glyph('0') == 0);
    assert(m4_font_glyph('9') == 9);
    assert(m4_font_glyph('a') == 16);
    assert(m4_font_glyph('A') == 17);
    assert(m4_font_glyph('z') == 66);
    assert(m4_font_glyph('Z') == 67);
    assert(m4_font_glyph('.') == 68);
    assert(m4_font_glyph(',') == 69);
    assert(m4_font_glyph('!') == 70);
    assert(m4_font_glyph('?') == 71);
    assert(m4_font_glyph(':') == 72);
    assert(m4_font_glyph('<') == 73);
    assert(m4_font_glyph('-') == 74);
    assert(m4_font_glyph(' ') == -1);
    assert(m4_font_glyph('#') == -1);
    return 0;
}
