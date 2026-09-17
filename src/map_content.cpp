#include "map_content.h"

#include <array>
#include <cstddef>

#include "progression_content.h"

namespace fh
{
namespace
{

constexpr std::array<MapTargetSpec, 16> TARGETS = {{
    {MapTarget::CrystalLake, Region::MariMari, "Crystal Lake", MapMarkerKind::Fishing, 152, 28,
     MapUnlock::Always, MapAction::Fishing, 1},
    {MapTarget::Pier, Region::MariMari, "Pier", MapMarkerKind::Fishing, 136, 84,
     MapUnlock::Always, MapAction::Fishing, 2},
    {MapTarget::ShopMariMari, Region::MariMari, "Shop", MapMarkerKind::Shop, 104, 20,
     MapUnlock::Always, MapAction::Shop, int(ShopId::MariMari)},
    {MapTarget::River, Region::MariMari, "River", MapMarkerKind::Fishing, 216, 20,
     MapUnlock::ClubCard, MapAction::Fishing, 3},
    {MapTarget::Ocean, Region::MariMari, "Ocean", MapMarkerKind::Fishing, 112, 132,
     MapUnlock::OldBoat, MapAction::Fishing, 4},
    {MapTarget::Cave, Region::MariMari, "Cave", MapMarkerKind::Fishing, 24, 100,
     MapUnlock::AncientMap, MapAction::Fishing, 5},
    {MapTarget::Lagoon, Region::MariMari, "Lagoon", MapMarkerKind::Fishing, 88, 37,
     MapUnlock::CaptainsHat, MapAction::Fishing, 6},
    {MapTarget::Beach, Region::MariMari, "Beach", MapMarkerKind::Fishing, 162, 97,
     MapUnlock::BeachBall, MapAction::None, 0},
    {MapTarget::Waterfall, Region::MariMari, "Waterfall", MapMarkerKind::Fishing, 140, 128,
     MapUnlock::OldBoat, MapAction::Fishing, 7},
    {MapTarget::Catalog, Region::MariMari, "Catalog", MapMarkerKind::Catalog, 12, 148,
     MapUnlock::Catalog, MapAction::Catalog, 0},
    {MapTarget::TravelMariMari, Region::MariMari, "Travel", MapMarkerKind::Travel, 233, 52,
     MapUnlock::CarKeys, MapAction::Travel, int(Region::JarimPerla), 2},

    {MapTarget::CityBeach, Region::JarimPerla, "City Beach", MapMarkerKind::Fishing, 127, 93,
     MapUnlock::Always, MapAction::Fishing, 8},
    {MapTarget::Bridge, Region::JarimPerla, "Bridge", MapMarkerKind::Fishing, 108, 27,
     MapUnlock::Always, MapAction::Fishing, 9},
    {MapTarget::Breakwater, Region::JarimPerla, "Breakwater", MapMarkerKind::Fishing, 162, 18,
     MapUnlock::JarimPerlaItem1, MapAction::Fishing, 10},
    {MapTarget::ShopJarimPerla, Region::JarimPerla, "Jarim Shop", MapMarkerKind::Shop, 141, 77,
     MapUnlock::Always, MapAction::Shop, int(ShopId::JarimPerla)},
    {MapTarget::TravelJarimPerla, Region::JarimPerla, "Travel", MapMarkerKind::Travel, 4, 49,
     MapUnlock::CarKeys, MapAction::Travel, int(Region::MariMari), 0},
}};

constexpr std::array<MapTarget, 11> MARI_MARI_TARGETS = {{
    MapTarget::CrystalLake,
    MapTarget::Pier,
    MapTarget::ShopMariMari,
    MapTarget::River,
    MapTarget::Ocean,
    MapTarget::Cave,
    MapTarget::Lagoon,
    MapTarget::Beach,
    MapTarget::Waterfall,
    MapTarget::Catalog,
    MapTarget::TravelMariMari,
}};

constexpr std::array<MapTarget, 5> JARIM_PERLA_TARGETS = {{
    MapTarget::CityBeach,
    MapTarget::Bridge,
    MapTarget::Breakwater,
    MapTarget::ShopJarimPerla,
    MapTarget::TravelJarimPerla,
}};

// D-pad navigation is an ordered nearest-first fallback table. A direction may
// name several candidates. FlowModel checks them in this order and selects the
// first target that is currently unlocked/visible. This lets a locked nearby
// spot fall through naturally to the next location without cycling.
struct MapRouteChoice
{
    Region region;
    MapTarget from;
    MapDirection direction;
    std::array<MapTarget, 3> candidates;
    int count;
};

constexpr std::array<MapRouteChoice, 32> MARI_MARI_ROUTE_CHOICES = {{
    {Region::MariMari, MapTarget::Lagoon, MapDirection::Up, {MapTarget::ShopMariMari, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Lagoon, MapDirection::Down, {MapTarget::Cave, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Lagoon, MapDirection::Right, {MapTarget::Pier, MapTarget::None, MapTarget::None}, 1},

    {Region::MariMari, MapTarget::Cave, MapDirection::Up, {MapTarget::Lagoon, MapTarget::ShopMariMari, MapTarget::None}, 2},
    {Region::MariMari, MapTarget::Cave, MapDirection::Right, {MapTarget::Ocean, MapTarget::Pier, MapTarget::None}, 2},

    {Region::MariMari, MapTarget::Waterfall, MapDirection::Up, {MapTarget::Pier, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Waterfall, MapDirection::Right, {MapTarget::Beach, MapTarget::TravelMariMari, MapTarget::None}, 2},
    {Region::MariMari, MapTarget::Waterfall, MapDirection::Left, {MapTarget::Ocean, MapTarget::None, MapTarget::None}, 1},

    {Region::MariMari, MapTarget::Beach, MapDirection::Up, {MapTarget::CrystalLake, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Beach, MapDirection::Down, {MapTarget::Waterfall, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Beach, MapDirection::Right, {MapTarget::TravelMariMari, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Beach, MapDirection::Left, {MapTarget::Pier, MapTarget::None, MapTarget::None}, 1},

    {Region::MariMari, MapTarget::ShopMariMari, MapDirection::Down, {MapTarget::Pier, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::ShopMariMari, MapDirection::Right, {MapTarget::CrystalLake, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::ShopMariMari, MapDirection::Left, {MapTarget::Lagoon, MapTarget::Cave, MapTarget::None}, 2},

    {Region::MariMari, MapTarget::Ocean, MapDirection::Up, {MapTarget::Pier, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Ocean, MapDirection::Right, {MapTarget::Waterfall, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Ocean, MapDirection::Left, {MapTarget::Cave, MapTarget::None, MapTarget::None}, 1},

    {Region::MariMari, MapTarget::Pier, MapDirection::Up, {MapTarget::CrystalLake, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Pier, MapDirection::Down, {MapTarget::Ocean, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Pier, MapDirection::Right, {MapTarget::Beach, MapTarget::TravelMariMari, MapTarget::None}, 2},
    {Region::MariMari, MapTarget::Pier, MapDirection::Left, {MapTarget::ShopMariMari, MapTarget::Lagoon, MapTarget::None}, 2},
    {Region::MariMari, MapTarget::Pier, MapDirection::UpLeft, {MapTarget::ShopMariMari, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::Pier, MapDirection::UpRight, {MapTarget::TravelMariMari, MapTarget::None, MapTarget::None}, 1},

    {Region::MariMari, MapTarget::CrystalLake, MapDirection::Down, {MapTarget::Pier, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::CrystalLake, MapDirection::Right, {MapTarget::River, MapTarget::TravelMariMari, MapTarget::None}, 2},
    {Region::MariMari, MapTarget::CrystalLake, MapDirection::Left, {MapTarget::ShopMariMari, MapTarget::None, MapTarget::None}, 1},

    {Region::MariMari, MapTarget::River, MapDirection::Down, {MapTarget::TravelMariMari, MapTarget::Beach, MapTarget::Pier}, 3},
    {Region::MariMari, MapTarget::River, MapDirection::Left, {MapTarget::CrystalLake, MapTarget::None, MapTarget::None}, 1},

    {Region::MariMari, MapTarget::TravelMariMari, MapDirection::Up, {MapTarget::River, MapTarget::None, MapTarget::None}, 1},
    {Region::MariMari, MapTarget::TravelMariMari, MapDirection::Down, {MapTarget::Beach, MapTarget::Pier, MapTarget::None}, 2},
    {Region::MariMari, MapTarget::TravelMariMari, MapDirection::Left, {MapTarget::CrystalLake, MapTarget::None, MapTarget::None}, 1},
}};

// Jarim Perla follows the user's red-line sketch. These connections are
// bidirectional, with direction chosen from the relative marker geometry.
constexpr std::array<MapRouteChoice, 8> JARIM_PERLA_ROUTE_CHOICES = {{
    {Region::JarimPerla, MapTarget::TravelJarimPerla, MapDirection::Right, {MapTarget::Bridge, MapTarget::None, MapTarget::None}, 1},
    {Region::JarimPerla, MapTarget::Bridge, MapDirection::Left, {MapTarget::TravelJarimPerla, MapTarget::None, MapTarget::None}, 1},
    {Region::JarimPerla, MapTarget::Bridge, MapDirection::Right, {MapTarget::Breakwater, MapTarget::None, MapTarget::None}, 1},
    {Region::JarimPerla, MapTarget::Breakwater, MapDirection::Left, {MapTarget::Bridge, MapTarget::None, MapTarget::None}, 1},
    {Region::JarimPerla, MapTarget::Bridge, MapDirection::DownRight, {MapTarget::ShopJarimPerla, MapTarget::None, MapTarget::None}, 1},
    {Region::JarimPerla, MapTarget::ShopJarimPerla, MapDirection::UpLeft, {MapTarget::Bridge, MapTarget::None, MapTarget::None}, 1},
    {Region::JarimPerla, MapTarget::ShopJarimPerla, MapDirection::DownLeft, {MapTarget::CityBeach, MapTarget::None, MapTarget::None}, 1},
    {Region::JarimPerla, MapTarget::CityBeach, MapDirection::UpRight, {MapTarget::ShopJarimPerla, MapTarget::None, MapTarget::None}, 1},
}};

template<std::size_t Size>
const MapRouteChoice* find_route_choice(const std::array<MapRouteChoice, Size>& routes,
                                        MapTarget from, MapDirection direction) noexcept
{
    for(const MapRouteChoice& route : routes)
    {
        if(route.from == from && route.direction == direction)
        {
            return &route;
        }
    }
    return nullptr;
}

const MapRouteChoice* route_choice(Region region, MapTarget from, MapDirection direction) noexcept
{
    switch(region)
    {
    case Region::MariMari:
        return find_route_choice(MARI_MARI_ROUTE_CHOICES, from, direction);
    case Region::JarimPerla:
        return find_route_choice(JARIM_PERLA_ROUTE_CHOICES, from, direction);
    }
    return nullptr;
}

}

const MapTargetSpec* map_target_spec(MapTarget target) noexcept
{
    for(const MapTargetSpec& spec : TARGETS)
    {
        if(spec.id == target)
        {
            return &spec;
        }
    }
    return nullptr;
}

int region_target_count(Region region) noexcept
{
    switch(region)
    {
    case Region::MariMari:
        return int(MARI_MARI_TARGETS.size());
    case Region::JarimPerla:
        return int(JARIM_PERLA_TARGETS.size());
    }
    return 0;
}

MapTarget region_target_at(Region region, int index) noexcept
{
    if(index < 0)
    {
        return MapTarget::None;
    }
    switch(region)
    {
    case Region::MariMari:
        return index < int(MARI_MARI_TARGETS.size()) ? MARI_MARI_TARGETS[index] : MapTarget::None;
    case Region::JarimPerla:
        return index < int(JARIM_PERLA_TARGETS.size()) ? JARIM_PERLA_TARGETS[index] : MapTarget::None;
    }
    return MapTarget::None;
}

MapTarget region_first_target(Region region) noexcept
{
    switch(region)
    {
    case Region::MariMari:
        return MapTarget::CrystalLake;
    case Region::JarimPerla:
        return MapTarget::CityBeach;
    }
    return MapTarget::CrystalLake;
}

int map_route_candidate_count(Region region, MapTarget from, MapDirection direction) noexcept
{
    const MapRouteChoice* choice = route_choice(region, from, direction);
    return choice ? choice->count : 0;
}

MapTarget map_route_candidate_at(Region region, MapTarget from, MapDirection direction, int index) noexcept
{
    const MapRouteChoice* choice = route_choice(region, from, direction);
    if(! choice || index < 0 || index >= choice->count)
    {
        return MapTarget::None;
    }
    return choice->candidates[index];
}

MapTarget map_route_target(Region region, MapTarget from, MapDirection direction) noexcept
{
    return map_route_candidate_at(region, from, direction, 0);
}

int map_marker_frame(MapTarget target, int animation_phase) noexcept
{
    const MapTargetSpec* spec = map_target_spec(target);
    if(! spec)
    {
        return 0;
    }

    const int phase = animation_phase == 0 ? 0 : 1;
    if(spec->marker_kind == MapMarkerKind::Travel)
    {
        return spec->marker_frame_base + phase;
    }
    return phase;
}

}
