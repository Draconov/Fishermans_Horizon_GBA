#include "map_content.h"

#include <array>

#include "progression_content.h"

namespace fh
{
namespace
{

constexpr std::array<MapTargetSpec, 16> TARGETS = {{
    {MapTarget::CrystalLake, Region::MariMari, "Crystal Lake", MapMarkerKind::Fishing, 152, 28,
     MapTarget::ShopMariMari, MapTarget::River, MapTarget::None, MapTarget::Pier,
     MapUnlock::Always, MapAction::Fishing, 1},
    {MapTarget::Pier, Region::MariMari, "Pier", MapMarkerKind::Fishing, 136, 84,
     MapTarget::Cave, MapTarget::Beach, MapTarget::CrystalLake, MapTarget::Waterfall,
     MapUnlock::Always, MapAction::Fishing, 2},
    {MapTarget::ShopMariMari, Region::MariMari, "Shop", MapMarkerKind::Shop, 104, 20,
     MapTarget::Cave, MapTarget::CrystalLake, MapTarget::TravelMariMari, MapTarget::Lagoon,
     MapUnlock::Always, MapAction::Shop, int(ShopId::MariMari)},
    {MapTarget::River, Region::MariMari, "River", MapMarkerKind::Fishing, 216, 20,
     MapTarget::CrystalLake, MapTarget::None, MapTarget::None, MapTarget::Beach,
     MapUnlock::ClubCard, MapAction::Fishing, 3},
    {MapTarget::Ocean, Region::MariMari, "Ocean", MapMarkerKind::Fishing, 112, 132,
     MapTarget::Cave, MapTarget::Waterfall, MapTarget::Pier, MapTarget::None,
     MapUnlock::OldBoat, MapAction::Fishing, 4},
    {MapTarget::Cave, Region::MariMari, "Cave", MapMarkerKind::Fishing, 24, 100,
     MapTarget::None, MapTarget::Pier, MapTarget::Lagoon, MapTarget::Ocean,
     MapUnlock::AncientMap, MapAction::Fishing, 5},
    {MapTarget::Lagoon, Region::MariMari, "Lagoon", MapMarkerKind::Fishing, 88, 37,
     MapTarget::Cave, MapTarget::CrystalLake, MapTarget::ShopMariMari, MapTarget::Pier,
     MapUnlock::CaptainsHat, MapAction::Fishing, 6},
    {MapTarget::Beach, Region::MariMari, "Beach", MapMarkerKind::Fishing, 162, 97,
     MapTarget::Pier, MapTarget::None, MapTarget::River, MapTarget::Waterfall,
     MapUnlock::BeachBall, MapAction::None, 0},
    {MapTarget::Waterfall, Region::MariMari, "Waterfall", MapMarkerKind::Fishing, 140, 128,
     MapTarget::Ocean, MapTarget::Beach, MapTarget::Pier, MapTarget::None,
     MapUnlock::OldBoat, MapAction::Fishing, 7},
    {MapTarget::Catalog, Region::MariMari, "Catalog", MapMarkerKind::Catalog, 12, 148,
     MapTarget::None, MapTarget::None, MapTarget::None, MapTarget::CrystalLake,
     MapUnlock::Catalog, MapAction::Catalog, 0},
    {MapTarget::TravelMariMari, Region::MariMari, "Travel", MapMarkerKind::Travel, 233, 52,
     MapTarget::None, MapTarget::None, MapTarget::None, MapTarget::ShopMariMari,
     MapUnlock::CarKeys, MapAction::Travel, int(Region::JarimPerla), 2},

    {MapTarget::CityBeach, Region::JarimPerla, "City Beach", MapMarkerKind::Fishing, 127, 93,
     MapTarget::None, MapTarget::Bridge, MapTarget::None, MapTarget::TravelJarimPerla,
     MapUnlock::Always, MapAction::Fishing, 8},
    {MapTarget::Bridge, Region::JarimPerla, "Bridge", MapMarkerKind::Fishing, 108, 27,
     MapTarget::CityBeach, MapTarget::ShopJarimPerla, MapTarget::None, MapTarget::Breakwater,
     MapUnlock::Always, MapAction::Fishing, 9},
    {MapTarget::Breakwater, Region::JarimPerla, "Breakwater", MapMarkerKind::Fishing, 162, 18,
     MapTarget::TravelJarimPerla, MapTarget::ShopJarimPerla, MapTarget::Bridge, MapTarget::None,
     MapUnlock::JarimPerlaItem1, MapAction::Fishing, 10},
    {MapTarget::ShopJarimPerla, Region::JarimPerla, "Jarim Shop", MapMarkerKind::Shop, 141, 77,
     MapTarget::Bridge, MapTarget::None, MapTarget::None, MapTarget::Breakwater,
     MapUnlock::Always, MapAction::Shop, int(ShopId::JarimPerla)},
    {MapTarget::TravelJarimPerla, Region::JarimPerla, "Travel", MapMarkerKind::Travel, 4, 49,
     MapTarget::None, MapTarget::Breakwater, MapTarget::CityBeach, MapTarget::None,
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
