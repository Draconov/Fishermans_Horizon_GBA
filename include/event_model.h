#ifndef FH_EVENT_MODEL_H
#define FH_EVENT_MODEL_H

namespace fh
{

class FlowModel;

class EventModel
{
public:
    explicit EventModel(int event_id) noexcept;

    [[nodiscard]] int id() const noexcept;
    [[nodiscard]] const char* text() const noexcept;
    void begin(FlowModel& flow) const noexcept;
    void complete(FlowModel& flow) const noexcept;

private:
    int _event_id;
};

}

#endif
