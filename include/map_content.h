#ifndef FH_MAP_CONTENT_H
#define FH_MAP_CONTENT_H

namespace fh
{

enum class Region
{
    MariMari = 0,
    JarimPerla = 1,
};

enum class MapTarget
{
    None = -1,

    CrystalLake,
    Pier,
    ShopMariMari,
    Shop = ShopMariMari,
    River,
    Ocean,
    Cave,
    Lagoon,
    Beach,
    Waterfall,
    Catalog,
    TravelMariMari,

    CityBeach,
    Bridge,
    Breakwater,
    ShopJarimPerla,
    TravelJarimPerla,
};

enum class MapMarkerKind
{
    Fishing,
    Shop,
    Travel,
    Catalog,
};

enum class MapUnlock
{
    Always,
    ClubCard,
    OldBoat,
    AncientMap,
    Catalog,
    CaptainsHat,
    BeachBall,
    CarKeys,
    JarimPerlaItem1,
};

enum class MapAction
{
    None,
    Fishing,
    Shop,
    Travel,
    Catalog,
};

struct MapTargetSpec
{
    MapTarget id;
    Region region;
    const char* label;
    MapMarkerKind marker_kind;
    int screen_x;
    int screen_y;
    MapTarget left;
    MapTarget right;
    MapTarget up;
    MapTarget down;
    MapUnlock unlock;
    MapAction action;
    int action_value;
    int marker_frame_base = 0;
};

[[nodiscard]] const MapTargetSpec* map_target_spec(MapTarget target) noexcept;
[[nodiscard]] int region_target_count(Region region) noexcept;
[[nodiscard]] MapTarget region_target_at(Region region, int index) noexcept;
[[nodiscard]] MapTarget region_first_target(Region region) noexcept;
[[nodiscard]] int map_marker_frame(MapTarget target, int animation_phase) noexcept;

}

#endif
