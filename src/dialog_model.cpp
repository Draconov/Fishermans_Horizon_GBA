#include "dialog_model.h"


#include "dialog_layout.h"

namespace fh
{

DialogModel::DialogModel(const char* text) noexcept
{
    start(text);
}

void DialogModel::start(const char* text) noexcept
{
    _text = text ? text : "";
    _text_length = 0;
    const volatile char* text_cursor = _text;
    while(*text_cursor)
    {
        ++_text_length;
        ++text_cursor;
    }
    _box_y = 160;
    _source_index = 0;
    _page_start = 0;
    _page_index = 0;
    _active = true;
    _waiting = false;
    _dismiss = false;
    _done = false;
    _set_new_page();
}

void DialogModel::clear() noexcept
{
    _text = "";
    _text_length = 0;
    _box_y = 160;
    _cursor_x = 8;
    _cursor_y = 4;
    _source_index = 0;
    _page_start = 0;
    _page_index = 0;
    _active = false;
    _waiting = false;
    _dismiss = false;
    _done = false;
}

DialogEvent DialogModel::update(bool advance_pressed) noexcept
{
    if(! _active || _done)
    {
        return DialogEvent::None;
    }

    if(_dismiss)
    {
        if(_box_y < 160)
        {
            _box_y += 2;
        }
        if(_box_y >= 160)
        {
            _box_y = 160;
            _active = false;
            _done = true;
            return DialogEvent::Closed;
        }
        return DialogEvent::None;
    }

    if(_box_y > 136)
    {
        _box_y -= 2;
        return DialogEvent::None;
    }

    if(_waiting)
    {
        if(! advance_pressed)
        {
            return DialogEvent::None;
        }

        if(_source_index < _length() && _cursor_y > 13)
        {
            ++_page_index;
            _page_start = _source_index;
            _set_new_page();
            _waiting = false;
        }
        else if(_source_index >= _length())
        {
            _dismiss = true;
            _waiting = false;
        }
        return DialogEvent::NextPage;
    }

    if(_source_index < _length() && _cursor_y < 22)
    {
        const char character = _text[_source_index];
        _consume_character(character);
        ++_source_index;

        dialog_apply_line_cutoff(_cursor_x, _cursor_y);
    }

    if(_source_index >= _length() || (_source_index < _length() && _cursor_y > 13))
    {
        _waiting = true;
    }

    return DialogEvent::None;
}

const char* DialogModel::text() const noexcept
{
    return _text;
}

int DialogModel::box_y() const noexcept
{
    return _box_y;
}

int DialogModel::cursor_x() const noexcept
{
    return _cursor_x;
}

int DialogModel::cursor_y() const noexcept
{
    return _cursor_y;
}

int DialogModel::page_index() const noexcept
{
    return _page_index;
}

int DialogModel::page_start() const noexcept
{
    return _page_start;
}

int DialogModel::visible_end() const noexcept
{
    return _source_index;
}

bool DialogModel::active() const noexcept
{
    return _active;
}

bool DialogModel::waiting_for_advance() const noexcept
{
    return _waiting;
}

bool DialogModel::dismissing() const noexcept
{
    return _dismiss;
}

bool DialogModel::done() const noexcept
{
    return _done;
}

bool DialogModel::talking() const noexcept
{
    return _active && ! _waiting && ! _dismiss && _box_y == 136 && _source_index < _text_length;
}

void DialogModel::_set_new_page() noexcept
{
    _cursor_x = 8;
    _cursor_y = 4;
}

void DialogModel::_consume_character(char character) noexcept
{
    dialog_consume_character(character, _cursor_x, _cursor_y);
}

int DialogModel::_length() const noexcept
{
    return _text_length;
}

}
