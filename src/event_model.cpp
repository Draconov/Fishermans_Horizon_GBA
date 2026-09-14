#include "event_model.h"

#include "flow_model.h"

namespace fh
{
namespace
{

constexpr const char* PROLOGUE_TEXT =
    "Hya! I<m Cecil!##Welcome to Mari-Mari!##Here you<ll find the most weird sea creatures in the world!#"
    "You know, fishing is pretty simple.#I hope you enjoy your time around here!#If you need anything, come visit me "
    "at the shop!#See ya!";

constexpr const char* ENDING_TEXT =
    "Hya! How are you doing?!## WOW! You caught all the known sea creatures of Mari-Mari!# That<s amazing!##"
    "I hope you enjoyed your time here.#Thanks for playing!##See ya!";

}

EventModel::EventModel(int event_id) noexcept :
    _event_id(event_id)
{
}

int EventModel::id() const noexcept
{
    return _event_id;
}

const char* EventModel::text() const noexcept
{
    switch(_event_id)
    {
    case 1:
        return PROLOGUE_TEXT;
    case 2:
        return ENDING_TEXT;
    default:
        return "";
    }
}

void EventModel::begin(FlowModel& flow) const noexcept
{
    flow.begin_event_dialog(_event_id);
}

void EventModel::complete(FlowModel& flow) const noexcept
{
    flow.complete_event();
}

}
