#include "options_model.h"

#include "flow_model.h"

namespace fh
{

int OptionsModel::sound(const FlowModel& flow) const noexcept
{
    return flow.sound_option();
}

void OptionsModel::toggle_sound(FlowModel& flow) const noexcept
{
    flow.toggle_sound_option();
}

void OptionsModel::back(FlowModel& flow) const noexcept
{
    flow.handle_options_back();
}

}
