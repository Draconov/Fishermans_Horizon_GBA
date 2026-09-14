#include <cassert>

#include "flow_model.h"
#include "options_model.h"

int main()
{
    {
        fh::ProgressState progress;
        fh::FlowModel flow(progress);
        fh::OptionsModel options;
        assert(options.sound(flow) == 1);
        options.toggle_sound(flow);
        assert(options.sound(flow) == 0);
        options.toggle_sound(flow);
        assert(options.sound(flow) == 1);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        fh::FlowModel flow(progress);
        flow.complete_intro();
        flow.handle_title_command(fh::TitleCommand::Options);
        assert(flow.state() == fh::GameState::Options);
        fh::OptionsModel options;
        options.back(flow);
        assert(flow.state() == fh::GameState::Title);
    }

    return 0;
}
