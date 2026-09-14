#ifndef FH_DIALOG_MODEL_H
#define FH_DIALOG_MODEL_H

#include <cstddef>

namespace fh
{

enum class DialogEvent
{
    None,
    NextPage,
    Closed,
};

class DialogModel
{
public:
    DialogModel() noexcept = default;
    explicit DialogModel(const char* text) noexcept;

    void start(const char* text) noexcept;
    [[nodiscard]] DialogEvent update(bool advance_pressed) noexcept;

    [[nodiscard]] const char* text() const noexcept;
    [[nodiscard]] int box_y() const noexcept;
    [[nodiscard]] int cursor_x() const noexcept;
    [[nodiscard]] int cursor_y() const noexcept;
    [[nodiscard]] int page_index() const noexcept;
    [[nodiscard]] int page_start() const noexcept;
    [[nodiscard]] int visible_end() const noexcept;
    [[nodiscard]] bool active() const noexcept;
    [[nodiscard]] bool waiting_for_advance() const noexcept;
    [[nodiscard]] bool dismissing() const noexcept;
    [[nodiscard]] bool done() const noexcept;

private:
    void _set_new_page() noexcept;
    void _consume_character(char character) noexcept;
    [[nodiscard]] int _length() const noexcept;

    const char* _text = "";
    int _box_y = 160;
    int _cursor_x = 8;
    int _cursor_y = 4;
    int _source_index = 0;
    int _page_start = 0;
    int _page_index = 0;
    bool _active = false;
    bool _waiting = false;
    bool _dismiss = false;
    bool _done = false;
};

}

#endif
