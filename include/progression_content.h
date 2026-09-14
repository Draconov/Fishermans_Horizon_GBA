#ifndef FH_PROGRESSION_CONTENT_H
#define FH_PROGRESSION_CONTENT_H

namespace fh
{

enum class ShopEffect
{
    Bait,
    Rod,
    OldBoat,
    ClubCard,
    AncientMap,
    Catalog,
    Character,
};

enum class ShopPurchaseResult
{
    Purchased,
    SoldOut,
    InsufficientFunds,
    InvalidItem,
};

struct ShopItemSpec
{
    int slot;
    const char* name;
    const char* description;
    int price;
    ShopEffect effect;
    int effect_value;
};

[[nodiscard]] int shop_item_count() noexcept;
[[nodiscard]] const ShopItemSpec* shop_item_spec(int slot) noexcept;

}

#endif
