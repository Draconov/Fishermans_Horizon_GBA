#ifndef FH_OPTIONS_MODEL_H
#define FH_OPTIONS_MODEL_H

namespace fh
{

class FlowModel;

class OptionsModel
{
public:
    [[nodiscard]] int sound(const FlowModel& flow) const noexcept;
    void toggle_sound(FlowModel& flow) const noexcept;
    void back(FlowModel& flow) const noexcept;
};

}

#endif
