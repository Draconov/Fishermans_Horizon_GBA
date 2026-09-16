#include "catalog_content.h"

#include <array>

namespace fh
{
namespace
{

constexpr std::array<CatalogEntrySpec, 44> CATALOG_ENTRIES = {{
    {0, 3, "BOOT", "An old boot. Please, discard it properly."},
    {1, 4, "CAN", "An empty can. Please, discard it properly."},
    {2, 5, "PLASTIC BAG", "A plastic bag. Please, discard it properly."},
    {3, 1, "SIRIRIDINE", "A kind of sardine."},
    {4, 2, "DRAGFISH", "This fish likes heavy makeup."},
    {5, 6, "BLEH", "People often say its name after eating it for the first time."},
    {6, 7, "CLOWNFISH", "It uses its big red nose to eat."},
    {7, 8, "BAFU", "Fuba<s brother."},
    {8, 9, "HUNDAIA", "A hundred feet lacraia."},
    {9, 10, "UMADBRO", "Don<t you?"},
    {10, 11, "ANGELINE", "Legend says this fish fell from the heavens."},
    {11, 12, "GREENKISSER", "It likes to kiss woman."},
    {12, 13, "BLUEKISSER", "It likes to kiss man."},
    {13, 14, "YELLOWKISSER", "It likes to kiss children."},
    {14, 15, "ANONSTAR", "A starfish that likes anonymity."},
    {15, 16, "FUBA", "Bafu<s brother."},
    {16, 17, "SLIMEFISH", "A Slime that make its way into the ocean."},
    {17, 18, "GRABCRAB", "This crab grabs anything in its way."},
    {18, 19, "WHITESTRIPE", "A delicious fish, used in many cocktails."},
    {19, 20, "LEAFISH", "A fish that resembles a leaf."},
    {20, 21, "ILL-EEL", "Its color make it looks sick."},
    {21, 22, "SHRAMP", "A Shrimp with a sound amp."},
    {22, 23, "LAMBARI", "A common Lambari."},
    {23, 24, "PUG", "Also know as ghost fish."},
    {24, 25, "SHELLIPOP", "Lick it! It<s sweet!"},
    {25, 26, "BABY EYEGG", "A baby of a peculiar sea creature."},
    {26, 27, "EYEGG", "A very weird sea creature. It is said that it monitors the sea life."},
    {27, 28, "LARVA", "Not much is known about this creature."},
    {28, 29, "CONDOM", "This fish<s scale is used to make condoms."},
    {29, 30, "NOTTODAY", "Nor tomorrow..."},
    {30, 31, "BURP", "It does all the time."},
    {31, 32, "SIXTOPUS", "A six legged sea creature."},
    {32, 33, "TROLLSHARK", "A shark that mocks all the sea creatures."},
    {33, 34, "NUMKITE", "A numb fish shaped as a kite."},
    {34, 35, "NUMEART", "A numb fish shaped as a heart."},
    {35, 36, "STAREXIC", "An anorexic starfish."},
    {36, 37, "SHARK", "A common shark. It seems short, but very ferocious."},
    {37, 38, "PINKSHARK", "People are uncertain of its sexual alignment."},
    {38, 39, "HAMMERHEAD", "A very danger shark."},
    {39, 40, "BABY UNICUDA", "The baby of an amazing fish."},
    {40, 41, "UNICUDA", "The amazing unicorn fish!"},
    {41, 42, "SYNAMELL", "A caramel stoned fish. You cool?"},
    {42, 43, "CRYSTALINE", "An enchanted fish that habits the deeps of a cavern."},
    {43, 44, "???", "It seems to be a glitch in the game..."},
}};

}

int catalog_entry_count() noexcept
{
    return int(CATALOG_ENTRIES.size());
}

const CatalogEntrySpec* catalog_entry_spec(int cursor) noexcept
{
    if(cursor < 0 || cursor >= int(CATALOG_ENTRIES.size()))
    {
        return nullptr;
    }
    return &CATALOG_ENTRIES[cursor];
}

int catalog_slot_screen_x(int cursor) noexcept
{
    return 39 + (cursor % 11) * 16;
}

int catalog_slot_screen_y(int cursor) noexcept
{
    return 39 + (cursor / 11) * 24;
}

int catalog_fish_screen_x(int cursor) noexcept
{
    return catalog_slot_screen_x(cursor) + 1;
}

int catalog_fish_screen_y(int cursor) noexcept
{
    return catalog_slot_screen_y(cursor) + 5;
}

}
