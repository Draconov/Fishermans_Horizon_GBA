#ifndef FH_PRESENTATION_EFFECTS_H
#define FH_PRESENTATION_EFFECTS_H

namespace fh
{

enum class PresentationMode
{
    None = 0,
    FadeIn = 1,
    FadeOut = 2,
    FlashIn = 3,
    FlashOut = 4,
};

struct PresentationColor
{
    int red;
    int green;
    int blue;

    friend constexpr bool operator==(PresentationColor a, PresentationColor b) noexcept
    {
        return a.red == b.red && a.green == b.green && a.blue == b.blue;
    }
};

class PresentationEffects
{
public:
    void start_fade_in() noexcept;
    void start_fade_out() noexcept;
    void start_flash() noexcept;
    void update() noexcept;

    [[nodiscard]] PresentationMode mode() const noexcept;
    [[nodiscard]] int alpha() const noexcept;
    [[nodiscard]] PresentationColor color() const noexcept;
    [[nodiscard]] int flash_ticks() const noexcept;
    [[nodiscard]] bool black_screen() const noexcept;
    [[nodiscard]] bool active() const noexcept;

private:
    PresentationMode _mode = PresentationMode::None;
    PresentationColor _color{25, 5, 36};
    int _alpha = 255;
    int _flash_ticks = 0;
    bool _black_screen = true;
};

}

#endif
