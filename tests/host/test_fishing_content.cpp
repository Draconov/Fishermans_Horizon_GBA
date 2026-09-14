#include <cassert>
#include <cstdint>
#include <cstring>

#include "fishing_content.h"

namespace
{

void hash_byte(std::uint64_t& hash, unsigned char value)
{
    hash ^= value;
    hash *= 1099511628211ULL;
}

void hash_int(std::uint64_t& hash, int value)
{
    std::uint32_t encoded = static_cast<std::uint32_t>(value);
    for(int shift = 0; shift < 32; shift += 8)
    {
        hash_byte(hash, static_cast<unsigned char>((encoded >> shift) & 0xFF));
    }
}

void hash_string(std::uint64_t& hash, const char* text)
{
    while(*text)
    {
        hash_byte(hash, static_cast<unsigned char>(*text++));
    }
    hash_byte(hash, 0);
}

}

int main()
{
    assert(fh::fishing_area_count() == 5);
    assert(fh::fishing_area_spec(0).pool == 1);
    assert(fh::fishing_area_spec(99).pool == 1);

    assert(std::strcmp(fh::fish_for_roll(1, 1)->name, "BOOT") == 0);
    assert(std::strcmp(fh::fish_for_roll(2, 9)->name, "TROLLSHARK") == 0);
    assert(std::strcmp(fh::fish_for_roll(3, 9)->name, "PINKSHARK") == 0);
    assert(std::strcmp(fh::fish_for_roll(4, 9)->name, "HAMMERHEAD") == 0);
    assert(std::strcmp(fh::fish_for_roll(5, 9)->name, "???") == 0);
    assert(fh::fish_for_roll(1, 0) == nullptr);
    assert(fh::fish_for_roll(5, 10) == nullptr);

    std::uint64_t hash = 1469598103934665603ULL;
    for(int pool = 1; pool <= fh::fishing_area_count(); ++pool)
    {
        const fh::FishingAreaSpec& area = fh::fishing_area_spec(pool);
        hash_int(hash, area.pool);
        for(int roll = 1; roll <= 9; ++roll)
        {
            const fh::FishSpec* fish = fh::fish_for_roll(pool, roll);
            assert(fish);
            hash_string(hash, fish->name);
            hash_int(hash, fish->number);
            hash_int(hash, fish->difficulty);
            hash_int(hash, fish->bait);
            hash_int(hash, fish->movement);
            hash_int(hash, fish->distance);
            hash_int(hash, fish->sprite);
            hash_int(hash, fish->reward);
        }
    }
    assert(hash == 0x5DBBF209D221CEB3ULL);

    return 0;
}
