#include <cassert>

#include "flow_model.h"
#include "intro_model.h"

int main()
{
    fh::ProgressState progress;
    fh::FlowModel flow(progress);
    assert(flow.state() == fh::GameState::Intro);

    fh::IntroModel intro;
    assert(! intro.done());
    assert(intro.ticks() == 0);

    for(int frame = 1; frame < 25; ++frame)
    {
        assert(intro.update() == fh::IntroEvent::None);
    }
    assert(intro.ticks() == 24);
    assert(intro.update() == fh::IntroEvent::FadeInAndSound);
    assert(intro.ticks() == 25);

    while(intro.ticks() < 174)
    {
        assert(intro.update() == fh::IntroEvent::None);
    }
    assert(intro.update() == fh::IntroEvent::FadeOut);
    assert(intro.ticks() == 175);

    while(! intro.done())
    {
        const fh::IntroEvent event = intro.update();
        assert(event == fh::IntroEvent::None || event == fh::IntroEvent::Complete);
    }
    assert(intro.ticks() == 192);
    intro.complete(flow);
    assert(flow.state() == fh::GameState::Title);

    return 0;
}
