#ifndef FH_CATALOG_MODEL_H
#define FH_CATALOG_MODEL_H

#include "catalog_content.h"

namespace fh
{

class FlowModel;

enum class CatalogSection
{
    MariMari = 0,
    CoastalCity = 1,
};

class CatalogModel
{
public:
    [[nodiscard]] int selected_cursor() const noexcept;
    [[nodiscard]] int local_slot() const noexcept;
    [[nodiscard]] CatalogSection section() const noexcept;
    [[nodiscard]] const CatalogEntrySpec* selected_entry() const noexcept;
    [[nodiscard]] bool selected_caught(const FlowModel& flow) const noexcept;
    [[nodiscard]] bool complete(const FlowModel& flow) const noexcept;

    void next() noexcept;
    void previous() noexcept;
    void move_left() noexcept;
    void move_right() noexcept;
    void move_up() noexcept;
    void move_down() noexcept;
    void next_section() noexcept;
    void previous_section() noexcept;
    void select(int cursor) noexcept;

private:
    void _select_section_column(CatalogSection section, int column) noexcept;

    int _selected_cursor = 0;
    CatalogSection _section = CatalogSection::MariMari;
};

}

#endif
