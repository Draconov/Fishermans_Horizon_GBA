#include "catalog_model.h"

#include "flow_model.h"

namespace fh
{

int CatalogModel::selected_cursor() const noexcept
{
    return _selected_cursor;
}

const CatalogEntrySpec* CatalogModel::selected_entry() const noexcept
{
    return catalog_entry_spec(_selected_cursor);
}

bool CatalogModel::selected_caught(const FlowModel& flow) const noexcept
{
    const CatalogEntrySpec* entry = selected_entry();
    return entry && flow.catalog_has_fish(entry->fish_number);
}

bool CatalogModel::complete(const FlowModel& flow) const noexcept
{
    for(int fish_number = 1; fish_number <= 44; ++fish_number)
    {
        if(! flow.catalog_has_fish(fish_number))
        {
            return false;
        }
    }
    return true;
}

void CatalogModel::next() noexcept
{
    _selected_cursor = (_selected_cursor + 1) % catalog_entry_count();
}

void CatalogModel::previous() noexcept
{
    _selected_cursor = (_selected_cursor + catalog_entry_count() - 1) % catalog_entry_count();
}

void CatalogModel::move_left() noexcept
{
    if(_selected_cursor % 11 > 0)
    {
        --_selected_cursor;
    }
}

void CatalogModel::move_right() noexcept
{
    if(_selected_cursor % 11 < 10 && _selected_cursor + 1 < catalog_entry_count())
    {
        ++_selected_cursor;
    }
}

void CatalogModel::move_up() noexcept
{
    if(_selected_cursor >= 11)
    {
        _selected_cursor -= 11;
    }
}

void CatalogModel::move_down() noexcept
{
    if(_selected_cursor + 11 < catalog_entry_count())
    {
        _selected_cursor += 11;
    }
}

void CatalogModel::select(int cursor) noexcept
{
    if(cursor >= 0 && cursor < catalog_entry_count())
    {
        _selected_cursor = cursor;
    }
}

}
