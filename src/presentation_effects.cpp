#include "presentation_effects.h"

namespace fh
{

void PresentationEffects::start_fade_in() noexcept
{
    _color = {25, 5, 36};
    _mode = PresentationMode::FadeIn;
}

void PresentationEffects::start_fade_out() noexcept
{
    _color = {25, 5, 36};
    _mode = PresentationMode::FadeOut;
    _black_screen = false;
}

void PresentationEffects::start_flash() noexcept
{
    _color = {235, 255, 237};
    _mode = PresentationMode::FlashIn;
    _flash_ticks = 0;
}

void PresentationEffects::update() noexcept
{
    switch(_mode)
    {
    case PresentationMode::None:
        break;
    case PresentationMode::FadeIn:
        _alpha -= 15;
        if(_alpha <= 0)
        {
            _alpha = 0;
            _mode = PresentationMode::None;
            _black_screen = false;
        }
        break;
    case PresentationMode::FadeOut:
        _alpha += 15;
        if(_alpha >= 255)
        {
            _alpha = 255;
            _mode = PresentationMode::None;
            _black_screen = true;
        }
        break;
    case PresentationMode::FlashIn:
        _alpha += 150;
        if(_alpha >= 255)
        {
            _alpha = 255;
            _mode = PresentationMode::FlashOut;
            _flash_ticks = 0;
        }
        break;
    case PresentationMode::FlashOut:
        ++_flash_ticks;
        if(_flash_ticks > 3)
        {
            _alpha -= 150;
            if(_alpha <= 0)
            {
                _alpha = 0;
                _flash_ticks = 0;
                _color = {25, 5, 36};
                _mode = PresentationMode::None;
                _black_screen = false;
            }
        }
        break;
    }
}

PresentationMode PresentationEffects::mode() const noexcept { return _mode; }
int PresentationEffects::alpha() const noexcept { return _alpha; }
PresentationColor PresentationEffects::color() const noexcept { return _color; }
int PresentationEffects::flash_ticks() const noexcept { return _flash_ticks; }
bool PresentationEffects::black_screen() const noexcept { return _black_screen; }
bool PresentationEffects::active() const noexcept { return _mode != PresentationMode::None; }

}
