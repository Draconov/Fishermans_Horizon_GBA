#ifndef FH_INTRO_MODEL_H
#define FH_INTRO_MODEL_H

namespace fh
{

class FlowModel;

enum class IntroEvent
{
    None,
    FadeInAndSound,
    FadeOut,
    Complete,
};

class IntroModel
{
public:
    [[nodiscard]] IntroEvent update() noexcept;
    [[nodiscard]] bool done() const noexcept;
    [[nodiscard]] int ticks() const noexcept;
    void complete(FlowModel& flow) const noexcept;
    void skip(FlowModel& flow) noexcept;

private:
    int _ticks = 0;
    bool _done = false;
};

}

#endif
