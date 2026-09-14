#include "intro_model.h"

#include "flow_model.h"

namespace fh
{

IntroEvent IntroModel::update() noexcept
{
    if(_done)
    {
        return IntroEvent::None;
    }

    ++_ticks;
    if(_ticks == 25)
    {
        return IntroEvent::FadeInAndSound;
    }
    if(_ticks == 175)
    {
        return IntroEvent::FadeOut;
    }
    // ScreenFlash fades from 0 to 255 by 15 each update after tick 175,
    // reaches black on tick 191, and GameIntro observes blackScreen on 192.
    if(_ticks == 192)
    {
        _done = true;
        return IntroEvent::Complete;
    }
    return IntroEvent::None;
}

bool IntroModel::done() const noexcept
{
    return _done;
}

int IntroModel::ticks() const noexcept
{
    return _ticks;
}

void IntroModel::complete(FlowModel& flow) const noexcept
{
    if(_done)
    {
        flow.complete_intro();
    }
}

}
