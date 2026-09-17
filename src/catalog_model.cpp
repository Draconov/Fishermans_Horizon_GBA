#include "catalog_model.h"

#include "flow_model.h"

namespace fh
{
namespace
{

constexpr int COLUMNS = 11;
constexpr int MARI_MARI_COUNT = 44;
constexpr int JARIM_PERLA_START = 44;
constexpr int JARIM_PERLA_COUNT = 10;

}

int CatalogModel::selected_cursor() const noexcept { return _selected_cursor; }
CatalogSection CatalogModel::section() const noexcept { return _section; }
int CatalogModel::local_slot() const noexcept { return _section == CatalogSection::JarimPerla ? _selected_cursor - JARIM_PERLA_START : _selected_cursor; }
const CatalogEntrySpec* CatalogModel::selected_entry() const noexcept { return catalog_entry_spec(_selected_cursor); }

bool CatalogModel::selected_caught(const FlowModel& flow) const noexcept
{
    const CatalogEntrySpec* entry = selected_entry();
    return entry && flow.catalog_has_fish(entry->fish_number);
}

bool CatalogModel::complete(const FlowModel& flow) const noexcept
{
    for(int fish_number = 1; fish_number <= 54; ++fish_number)
    {
        if(! flow.catalog_has_fish(fish_number)) return false;
    }
    return true;
}

void CatalogModel::next() noexcept
{
    if(_section == CatalogSection::MariMari)
    {
        _selected_cursor = (_selected_cursor + 1) % MARI_MARI_COUNT;
    }
    else
    {
        _selected_cursor = JARIM_PERLA_START + ((_selected_cursor - JARIM_PERLA_START + 1) % JARIM_PERLA_COUNT);
    }
}

void CatalogModel::previous() noexcept
{
    if(_section == CatalogSection::MariMari)
    {
        _selected_cursor = (_selected_cursor + MARI_MARI_COUNT - 1) % MARI_MARI_COUNT;
    }
    else
    {
        _selected_cursor = JARIM_PERLA_START + ((_selected_cursor - JARIM_PERLA_START + JARIM_PERLA_COUNT - 1) % JARIM_PERLA_COUNT);
    }
}

void CatalogModel::move_left() noexcept
{
    const int local = local_slot();
    if(local % COLUMNS > 0) --_selected_cursor;
}

void CatalogModel::move_right() noexcept
{
    const int local = local_slot();
    const int section_count = _section == CatalogSection::MariMari ? MARI_MARI_COUNT : JARIM_PERLA_COUNT;
    if(local % COLUMNS < COLUMNS - 1 && local + 1 < section_count) ++_selected_cursor;
}

void CatalogModel::move_up() noexcept
{
    if(_section == CatalogSection::JarimPerla)
    {
        const int column = local_slot() % COLUMNS;
        _section = CatalogSection::MariMari;
        _selected_cursor = 33 + (column < 11 ? column : 10);
        if(_selected_cursor >= MARI_MARI_COUNT) _selected_cursor = MARI_MARI_COUNT - 1;
        return;
    }
    if(_selected_cursor >= COLUMNS) _selected_cursor -= COLUMNS;
}

void CatalogModel::move_down() noexcept
{
    if(_section == CatalogSection::MariMari)
    {
        const int candidate = _selected_cursor + COLUMNS;
        if(candidate < MARI_MARI_COUNT)
        {
            _selected_cursor = candidate;
            return;
        }
        const int column = _selected_cursor % COLUMNS;
        _section = CatalogSection::JarimPerla;
        _selected_cursor = JARIM_PERLA_START + (column < JARIM_PERLA_COUNT ? column : JARIM_PERLA_COUNT - 1);
        return;
    }
}

void CatalogModel::_select_section_column(CatalogSection section, int column) noexcept
{
    if(column < 0) column = 0;
    if(column >= COLUMNS) column = COLUMNS - 1;
    _section = section;
    if(section == CatalogSection::MariMari)
    {
        _selected_cursor = column;
    }
    else
    {
        if(column >= JARIM_PERLA_COUNT) column = JARIM_PERLA_COUNT - 1;
        _selected_cursor = JARIM_PERLA_START + column;
    }
}

void CatalogModel::next_section() noexcept
{
    const int column = local_slot() % COLUMNS;
    _select_section_column(_section == CatalogSection::MariMari ? CatalogSection::JarimPerla : CatalogSection::MariMari, column);
}

void CatalogModel::previous_section() noexcept
{
    next_section();
}

void CatalogModel::select(int cursor) noexcept
{
    if(cursor >= 0 && cursor < catalog_entry_count())
    {
        _selected_cursor = cursor;
        _section = cursor >= JARIM_PERLA_START ? CatalogSection::JarimPerla : CatalogSection::MariMari;
    }
}

}
