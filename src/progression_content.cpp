#include "progression_content.h"

#include <array>

namespace fh
{
namespace
{

constexpr std::array<ShopItemSpec, 16> SHOP_ITEMS = {{
    {0, "Bread", "A waterproof bread.", 15, ShopEffect::Bait, 1},
    {1, "Candy", "A candy suited to the taste of the sea creatures.", 15, ShopEffect::Bait, 2},
    {2, "Bitter Gum", "Did you know that some sea creatures like to chew a gum?", 30, ShopEffect::Bait, 3},
    {3, "Steak", "A delicious steak used to lure sharks.", 45, ShopEffect::Bait, 4},
    {4, "Rainboworm", "A very special bait. Some says it lures an amazing fish.", 100, ShopEffect::Bait, 5},
    {5, "Bait X", "A unique bait that lures all sea creatures.", 100, ShopEffect::Bait, 6},
    {6, "Pro Rod", "The rod used by many professionals.", 45, ShopEffect::Rod, 1},
    {7, "Nova Rod", "A brand new high tech rod!", 120, ShopEffect::Rod, 2},
    {8, "Old Boat", "My old boat. Good times, when I used to fish in the ocean.", 30, ShopEffect::OldBoat, 0},
    {9, "Club card", "Mari-Mari Fisherman<s Club card. You need to become a member to fish in the river.", 60,
     ShopEffect::ClubCard, 0},
    {10, "Ancient Map", "A copy of an ancient map that reveals a secret fishing spot.", 120,
     ShopEffect::AncientMap, 0},
    {11, "Catalog", "Keep record of the sea creatures you catch.", 20, ShopEffect::Catalog, 0},
    {12, "Leon", "This is Leon. He has his ups and downs, but he<s a nice pal. He<ll be glad to fish with you!", 30,
     ShopEffect::Character, 2},
    {13, "SGT Sazh", "This is an old friend of mine, STG. Sazh. He<ll be glad to fish with you!", 30,
     ShopEffect::Character, 3},
    {14, "Rosa", "This is Rosa, my granddaughter. She<ll be glad to fish with you!", 50, ShopEffect::Character, 4},
    {15, "Shadow", "This is Shadow, I don<t know him very well...", 100, ShopEffect::Character, 5},
}};

}

int shop_item_count() noexcept
{
    return int(SHOP_ITEMS.size());
}

const ShopItemSpec* shop_item_spec(int slot) noexcept
{
    if(slot < 0 || slot >= int(SHOP_ITEMS.size()))
    {
        return nullptr;
    }
    return &SHOP_ITEMS[slot];
}

}
