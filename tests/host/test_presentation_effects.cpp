#include <cassert>

#include "presentation_effects.h"

int main()
{
    using fh::PresentationColor;
    using fh::PresentationEffects;
    using fh::PresentationMode;

    PresentationEffects effects;
    assert(effects.mode() == PresentationMode::None);
    assert(effects.alpha() == 255);
    assert((effects.color() == PresentationColor{25, 5, 36}));
    assert(effects.black_screen());

    effects.start_fade_in();
    assert(effects.mode() == PresentationMode::FadeIn);
    assert(effects.black_screen());
    for(int index = 0; index < 16; ++index)
    {
        effects.update();
        assert(effects.mode() == PresentationMode::FadeIn);
        assert(effects.black_screen());
    }
    effects.update();
    assert(effects.mode() == PresentationMode::None);
    assert(effects.alpha() == 0);
    assert(! effects.black_screen());

    effects.start_fade_out();
    assert(effects.mode() == PresentationMode::FadeOut);
    for(int index = 0; index < 16; ++index)
    {
        effects.update();
        assert(! effects.black_screen());
    }
    effects.update();
    assert(effects.mode() == PresentationMode::None);
    assert(effects.alpha() == 255);
    assert(effects.black_screen());

    effects.start_fade_in();
    for(int index = 0; index < 17; ++index)
    {
        effects.update();
    }
    assert(effects.alpha() == 0);

    effects.start_flash();
    assert(effects.mode() == PresentationMode::FlashIn);
    assert((effects.color() == PresentationColor{235, 255, 237}));
    effects.update();
    assert(effects.alpha() == 150);
    assert(effects.mode() == PresentationMode::FlashIn);
    effects.update();
    assert(effects.alpha() == 255);
    assert(effects.mode() == PresentationMode::FlashOut);
    assert(effects.flash_ticks() == 0);

    for(int index = 0; index < 3; ++index)
    {
        effects.update();
        assert(effects.alpha() == 255);
        assert(effects.mode() == PresentationMode::FlashOut);
    }
    effects.update();
    assert(effects.alpha() == 105);
    effects.update();
    assert(effects.alpha() == 0);
    assert(effects.mode() == PresentationMode::None);
    assert((effects.color() == PresentationColor{25, 5, 36}));
    assert(effects.flash_ticks() == 0);
}
