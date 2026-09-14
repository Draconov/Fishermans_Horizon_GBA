#ifndef FH_CATALOG_MODEL_H
#define FH_CATALOG_MODEL_H

#include "catalog_content.h"

namespace fh
{

class FlowModel;

class CatalogModel
{
public:
    [[nodiscard]] int selected_cursor() const noexcept;
    [[nodiscard]] const CatalogEntrySpec* selected_entry() const noexcept;
    [[nodiscard]] bool selected_caught(const FlowModel& flow) const noexcept;
    [[nodiscard]] bool complete(const FlowModel& flow) const noexcept;

    void next() noexcept;
    void previous() noexcept;
    void select(int cursor) noexcept;

private:
    int _selected_cursor = 0;
};

}

#endif
