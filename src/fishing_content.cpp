#include "fishing_content.h"
namespace fh
{
namespace
{
constexpr std::array<FishingAreaSpec, 7> AREAS = {{
    {
        1,
        "graphic/background/crystalLake.png",
        {{
            {"BOOT", 3, 0, 7, 2, 40, 119, 1},
            {"BABY UNICUDA", 40, 1, 0, 1, 80, 122, 5},
            {"ANGELINE", 11, 1, 1, 1, 80, 129, 5},
            {"BLEH", 6, 1, 0, 1, 80, 131, 5},
            {"PUG", 24, 2, 3, 1, 80, 142, 10},
            {"WHITESTRIPE", 19, 2, 2, 1, 80, 137, 10},
            {"NUMKITE", 34, 2, 3, 1, 80, 144, 10},
            {"NUMEART", 35, 2, 2, 1, 80, 150, 10},
            {"UNICUDA", 41, 3, 5, 1, 80, 160, 25},
        }},
    },
    {
        2,
        "graphic/background/pier.png",
        {{
            {"CAN", 4, 0, 7, 2, 40, 120, 1},
            {"SIRIRIDINE", 1, 1, 0, 1, 80, 110, 5},
            {"DRAGFISH", 2, 1, 2, 1, 80, 111, 5},
            {"ANONSTAR", 15, 1, 1, 1, 80, 133, 5},
            {"SLIMEFISH", 17, 2, 3, 1, 80, 135, 10},
            {"GRABCRAB", 18, 2, 1, 1, 80, 136, 10},
            {"SHELLIPOP", 25, 2, 2, 1, 80, 143, 10},
            {"CONDOM", 29, 2, 2, 1, 80, 127, 10},
            {"TROLLSHARK", 33, 3, 4, 1, 80, 161, 25},
        }},
    },
    {
        3,
        "graphic/background/river.png",
        {{
            {"CLOWNFISH", 7, 1, 2, 1, 80, 123, 5},
            {"LARVA", 28, 1, 0, 1, 80, 146, 5},
            {"LEAFISH", 20, 2, 1, 1, 80, 138, 5},
            {"NOTTODAY", 30, 2, 0, 1, 80, 132, 10},
            {"GREENKISSER", 12, 3, 3, 1, 80, 130, 25},
            {"BLUEKISSER", 13, 3, 2, 1, 80, 152, 25},
            {"YELLOWKISSER", 14, 3, 1, 1, 80, 153, 25},
            {"HUNDAIA", 9, 2, 1, 1, 80, 163, 10},
            {"PINKSHARK", 38, 4, 4, 1, 80, 158, 50},
        }},
    },
    {
        4,
        "graphic/background/ocean.png",
        {{
            {"PLASTIC BAG", 5, 0, 7, 2, 40, 121, 1},
            {"SIRIRIDINE", 1, 1, 0, 1, 80, 110, 5},
            {"SHRAMP", 22, 1, 2, 1, 80, 151, 5},
            {"EYEGG", 27, 2, 1, 1, 80, 145, 10},
            {"BAFU", 8, 2, 3, 1, 80, 126, 10},
            {"LAMBARI", 23, 2, 0, 1, 80, 154, 10},
            {"SIXTOPUS", 32, 3, 2, 1, 80, 162, 25},
            {"SHARK", 37, 4, 4, 1, 80, 157, 50},
            {"HAMMERHEAD", 39, 4, 4, 1, 80, 159, 50},
        }},
    },
    {
        5,
        "graphic/background/cave.png",
        {{
            {"BABY EYEGG", 26, 1, 2, 1, 80, 140, 5},
            {"ILL-EEL", 21, 2, 0, 1, 80, 139, 5},
            {"BURP", 31, 2, 1, 1, 80, 155, 10},
            {"STAREXIC", 36, 2, 3, 1, 80, 149, 10},
            {"FUBA", 16, 2, 2, 1, 80, 134, 10},
            {"UMADBRO", 10, 2, 0, 1, 80, 128, 10},
            {"SYNAMELL", 42, 3, 2, 1, 80, 141, 25},
            {"CRYSTALINE", 43, 3, 3, 1, 80, 147, 25},
            {"???", 44, 4, 6, 1, 80, 148, 1},
        }},
    },
    {
        6,
        "graphics/fishing_bg_lagoon.bmp",
        {{
            {"CAN", 4, 0, 7, 2, 40, 120, 1},
            {"SIRIRIDINE", 1, 1, 0, 1, 80, 110, 5},
            {"DRAGFISH", 2, 1, 2, 1, 80, 111, 5},
            {"SHRAMP", 22, 1, 2, 1, 80, 151, 5},
            {"SLIMEFISH", 17, 2, 3, 1, 80, 135, 10},
            {"GRABCRAB", 18, 2, 1, 1, 80, 136, 10},
            {"SHELLIPOP", 25, 2, 2, 1, 80, 143, 10},
            {"LAMBARI", 23, 2, 0, 1, 80, 154, 10},
            {"TROLLSHARK", 33, 3, 4, 1, 80, 161, 25},
        }},
    },
    {
        7,
        "graphics/fishing_bg_waterfall.bmp",
        {{
            {"BOOT", 3, 0, 7, 2, 40, 119, 1},
            {"BABY UNICUDA", 40, 1, 0, 1, 80, 122, 5},
            {"ANGELINE", 11, 1, 1, 1, 80, 129, 5},
            {"LEAFISH", 20, 2, 1, 1, 80, 138, 5},
            {"HUNDAIA", 9, 2, 1, 1, 80, 163, 10},
            {"GREENKISSER", 12, 3, 3, 1, 80, 130, 25},
            {"BLUEKISSER", 13, 3, 2, 1, 80, 152, 25},
            {"NUMKITE", 34, 2, 3, 1, 80, 144, 10},
            {"UNICUDA", 41, 3, 5, 1, 80, 160, 25},
        }},
    },
}};

}

int fishing_area_count() noexcept
{
    return int(AREAS.size());
}

const FishingAreaSpec& fishing_area_spec(int pool) noexcept
{
    if(pool < 1 || pool > int(AREAS.size()))
    {
        return AREAS[0];
    }
    return AREAS[pool - 1];
}

const FishSpec* fish_for_roll(int pool, int roll) noexcept
{
    if(roll < 1 || roll > 9)
    {
        return nullptr;
    }
    return &fishing_area_spec(pool).fish[roll - 1];
}

}
