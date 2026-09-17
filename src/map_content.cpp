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

// The Mari-Mari route graph mirrors the approved red-line map sketch.
// A route is declared once, but each endpoint chooses the D-pad direction
// that feels most natural there. This allows dense nodes such as Pier to
// expose more than four direct neighbors without ambiguous cycling.
constexpr std::array<MapRoute, 14> MARI_MARI_ROUTES = {{
    {Region::MariMari, MapTarget::Lagoon, MapTarget::ShopMariMari, MapDirection::UpRight, MapDirection::DownLeft},
    {Region::MariMari, MapTarget::ShopMariMari, MapTarget::CrystalLake, MapDirection::Right, MapDirection::Left},
    {Region::MariMari, MapTarget::CrystalLake, MapTarget::River, MapDirection::Right, MapDirection::Left},
    {Region::MariMari, MapTarget::River, MapTarget::TravelMariMari, MapDirection::DownRight, MapDirection::UpLeft},
    {Region::MariMari, MapTarget::TravelMariMari, MapTarget::Beach, MapDirection::DownLeft, MapDirection::UpRight},
    {Region::MariMari, MapTarget::Beach, MapTarget::Waterfall, MapDirection::DownLeft, MapDirection::UpRight},
    {Region::MariMari, MapTarget::Waterfall, MapTarget::Ocean, MapDirection::Left, MapDirection::Right},
    {Region::MariMari, MapTarget::Ocean, MapTarget::Cave, MapDirection::UpLeft, MapDirection::DownRight},
    {Region::MariMari, MapTarget::Cave, MapTarget::Lagoon, MapDirection::UpRight, MapDirection::DownLeft},
    {Region::MariMari, MapTarget::Lagoon, MapTarget::Pier, MapDirection::Right, MapDirection::Left},
    {Region::MariMari, MapTarget::ShopMariMari, MapTarget::Pier, MapDirection::DownRight, MapDirection::UpLeft},
    {Region::MariMari, MapTarget::CrystalLake, MapTarget::Pier, MapDirection::Down, MapDirection::Up},
    {Region::MariMari, MapTarget::Pier, MapTarget::Beach, MapDirection::Right, MapDirection::Left},
    {Region::MariMari, MapTarget::Pier, MapTarget::Ocean, MapDirection::DownLeft, MapDirection::UpRight},
}};

// Preserve the existing Jarim Perla navigation while using the same generic graph format.
constexpr std::array<MapRoute, 6> JARIM_PERLA_ROUTES = {{
    {Region::JarimPerla, MapTarget::CityBeach, MapTarget::Bridge, MapDirection::Right, MapDirection::Left},
    {Region::JarimPerla, MapTarget::CityBeach, MapTarget::TravelJarimPerla, MapDirection::Down, MapDirection::Up},
    {Region::JarimPerla, MapTarget::Bridge, MapTarget::ShopJarimPerla, MapDirection::Right, MapDirection::Left},
    {Region::JarimPerla, MapTarget::Bridge, MapTarget::Breakwater, MapDirection::Down, MapDirection::Up},
    {Region::JarimPerla, MapTarget::Breakwater, MapTarget::TravelJarimPerla, MapDirection::Left, MapDirection::Right},
    {Region::JarimPerla, MapTarget::Breakwater, MapTarget::ShopJarimPerla, MapDirection::Right, MapDirection::Down},
}};

template<std::size_t Size>
MapTarget route_target(const std::array<MapRoute, Size>& routes, MapTarget from, MapDirection direction) noexcept
{
    for(const MapRoute& route : routes)
    {
        if(route.first == from && route.first_direction == direction)
        {
            return route.second;
        }
        if(route.second == from && route.second_direction == direction)
        {
            return route.first;
        }
    }
    return MapTarget::None;
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

MapTarget map_route_target(Region region, MapTarget from, MapDirection direction) noexcept
{
    switch(region)
    {
    case Region::MariMari:
        return route_target(MARI_MARI_ROUTES, from, direction);
    case Region::JarimPerla:
        return route_target(JARIM_PERLA_ROUTES, from, direction);
    }
    return MapTarget::None;
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
