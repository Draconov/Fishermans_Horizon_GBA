#ifndef FH_FISHING_CONTENT_H
#define FH_FISHING_CONTENT_H

#include <array>

namespace fh
{

struct FishSpec
{
    const char* name;
    int number;
    int difficulty;
    int bait;
    int movement;
    int distance;
    int sprite;
    int reward;
};

struct FishingAreaSpec
{
    int pool;
    const char* background_member;
    std::array<FishSpec, 9> fish;
};

[[nodiscard]] int fishing_area_count() noexcept;
[[nodiscard]] const FishingAreaSpec& fishing_area_spec(int pool) noexcept;
[[nodiscard]] const FishSpec* fish_for_roll(int pool, int roll) noexcept;

}

#endif
