#ifndef FH_CATALOG_CONTENT_H
#define FH_CATALOG_CONTENT_H

namespace fh
{

struct CatalogEntrySpec
{
    int cursor;
    int fish_number;
    const char* name;
    const char* description;
};

[[nodiscard]] int catalog_entry_count() noexcept;
[[nodiscard]] const CatalogEntrySpec* catalog_entry_spec(int cursor) noexcept;

}

#endif
