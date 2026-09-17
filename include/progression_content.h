#ifndef FH_PROGRESSION_CONTENT_H
#define FH_PROGRESSION_CONTENT_H

namespace fh
{

enum class ShopId
{
    MariMari = 0,
    JarimPerla = 1,
};

enum class ShopEffect
{
    Bait,
    Rod,
    OldBoat,
    ClubCard,
    AncientMap,
    Catalog,
    Character,
    CaptainsHat,
    BeachBall,
    CarKeys,
    JarimPerlaItem1,
};

enum class ShopPurchaseResult
{
    Purchased,
    SoldOut,
    Locked,
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

[[nodiscard]] int shop_item_count(ShopId shop) noexcept;
[[nodiscard]] const ShopItemSpec* shop_item_spec(ShopId shop, int slot) noexcept;

// Compatibility helpers for the original Mari-Mari shop.
[[nodiscard]] int shop_item_count() noexcept;
[[nodiscard]] const ShopItemSpec* shop_item_spec(int slot) noexcept;

}

#endif
