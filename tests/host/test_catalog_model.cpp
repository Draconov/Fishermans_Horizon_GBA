#include <array>
#include <cassert>
#include <cstring>

#include "catalog_content.h"
#include "catalog_model.h"
#include "flow_model.h"

int main()
{
    assert(fh::catalog_entry_count() == 44);

    constexpr std::array<int, 5> FIRST_NUMBERS = {3, 4, 5, 1, 2};
    constexpr std::array<const char*, 5> FIRST_NAMES = {"BOOT", "CAN", "PLASTIC BAG", "SIRIRIDINE", "DRAGFISH"};
    std::array<bool, 45> seen = {};
    for(int cursor = 0; cursor < 44; ++cursor)
    {
        const fh::CatalogEntrySpec* entry = fh::catalog_entry_spec(cursor);
        assert(entry);
        assert(entry->cursor == cursor);
        assert(entry->fish_number >= 1 && entry->fish_number <= 44);
        assert(! seen[entry->fish_number]);
        seen[entry->fish_number] = true;
        assert(entry->name && entry->name[0] != '\0');
        assert(entry->description && entry->description[0] != '\0');
        if(cursor < 5)
        {
            assert(entry->fish_number == FIRST_NUMBERS[cursor]);
            assert(std::strcmp(entry->name, FIRST_NAMES[cursor]) == 0);
        }
    }
    assert(fh::catalog_entry_spec(-1) == nullptr);
    assert(fh::catalog_entry_spec(44) == nullptr);
    const fh::CatalogEntrySpec* last = fh::catalog_entry_spec(43);
    assert(last && last->fish_number == 44);
    assert(std::strcmp(last->name, "???") == 0);

    fh::ProgressState progress;
    fh::FlowModel flow(progress);
    fh::CatalogModel catalog;
    assert(catalog.selected_cursor() == 0);
    assert(catalog.selected_entry()->fish_number == 3);
    assert(! catalog.selected_caught(flow));

    flow.apply_fishing_reward(3, 0);
    assert(catalog.selected_caught(flow));
    catalog.next();
    assert(catalog.selected_cursor() == 1);
    assert(catalog.selected_entry()->fish_number == 4);
    catalog.previous();
    assert(catalog.selected_cursor() == 0);
    catalog.previous();
    assert(catalog.selected_cursor() == 43);
    catalog.next();
    assert(catalog.selected_cursor() == 0);
    catalog.select(43);
    assert(catalog.selected_cursor() == 43);
    catalog.select(-1);
    assert(catalog.selected_cursor() == 43);
    catalog.select(44);
    assert(catalog.selected_cursor() == 43);

    assert(! catalog.complete(flow));
    for(int fish = 1; fish <= 44; ++fish)
    {
        flow.apply_fishing_reward(fish, 0);
    }
    assert(catalog.complete(flow));

    {
        fh::CatalogModel spatial;
        spatial.move_left();
        spatial.move_up();
        assert(spatial.selected_cursor() == 0);
        spatial.move_right();
        assert(spatial.selected_cursor() == 1);
        spatial.move_down();
        assert(spatial.selected_cursor() == 12);
        spatial.move_down();
        assert(spatial.selected_cursor() == 23);
        spatial.move_down();
        assert(spatial.selected_cursor() == 34);
        spatial.move_down();
        assert(spatial.selected_cursor() == 34);
        spatial.move_left();
        assert(spatial.selected_cursor() == 33);
        spatial.move_up();
        assert(spatial.selected_cursor() == 22);
        spatial.select(43);
        spatial.move_right();
        spatial.move_down();
        assert(spatial.selected_cursor() == 43);
    }

    return 0;
}
