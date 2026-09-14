#include <cassert>
#include <cstring>

#include "event_model.h"
#include "flow_model.h"

namespace
{

void enter_catalog(fh::FlowModel& flow)
{
    flow.handle_title_command(fh::TitleCommand::Play);
    assert(flow.state() == fh::GameState::Map);
    while(flow.selected_map_target() != fh::MapTarget::Catalog)
    {
        flow.handle_map_command(fh::MapCommand::NextTarget);
    }
    flow.handle_map_command(fh::MapCommand::Confirm);
    assert(flow.state() == fh::GameState::Catalog);
}

}

int main()
{
    {
        fh::ProgressState progress;
        progress.prologue_complete = false;
        fh::FlowModel flow(progress);
        flow.complete_intro();
        flow.handle_title_command(fh::TitleCommand::Play);
        assert(flow.state() == fh::GameState::Event);
        assert(flow.event_id() == 1);

        fh::EventModel event(flow.event_id());
        assert(event.id() == 1);
        assert(std::strstr(event.text(), "Cecil") != nullptr);
        event.begin(flow);
        assert(flow.event_id() == 1);
        event.complete(flow);
        assert(flow.state() == fh::GameState::Map);
        assert(flow.prologue_complete());
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.catalog = true;
        fh::FlowModel flow(progress);
        flow.complete_intro();
        enter_catalog(flow);
        flow.handle_catalog_back(true);
        assert(flow.state() == fh::GameState::Event);
        assert(flow.event_id() == 2);

        fh::EventModel ending(flow.event_id());
        assert(ending.id() == 2);
        assert(std::strstr(ending.text(), "caught all") != nullptr);
        ending.begin(flow);
        assert(flow.event_id() == 3);
        ending.complete(flow);
        assert(flow.state() == fh::GameState::Map);
        assert(flow.prologue_complete());

        // Event 3 blocks the all-fish ending from retriggering in the same runtime.
        while(flow.selected_map_target() != fh::MapTarget::Catalog)
        {
            flow.handle_map_command(fh::MapCommand::NextTarget);
        }
        flow.handle_map_command(fh::MapCommand::Confirm);
        assert(flow.state() == fh::GameState::Catalog);
        flow.handle_catalog_back(true);
        assert(flow.state() == fh::GameState::Map);
        assert(flow.event_id() == 3);
    }

    {
        fh::ProgressState progress;
        progress.prologue_complete = true;
        progress.catalog = true;
        fh::FlowModel flow(progress);
        flow.complete_intro();
        enter_catalog(flow);
        flow.handle_catalog_back(false);
        assert(flow.state() == fh::GameState::Map);
        assert(flow.event_id() == 0);
    }

    return 0;
}
