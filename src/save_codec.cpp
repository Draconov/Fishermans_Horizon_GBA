#include "save_codec.h"

#include <algorithm>

namespace fh
{
namespace
{

constexpr std::size_t HEADER_SIZE = 12;
constexpr std::uint8_t MAGIC[4] = {'F', 'H', 'G', 'S'};

void write_u16(std::array<std::uint8_t, SAVE_IMAGE_SIZE>& bytes, std::size_t offset, std::uint16_t value) noexcept
{
    bytes[offset] = std::uint8_t(value & 0xFF);
    bytes[offset + 1] = std::uint8_t((value >> 8) & 0xFF);
}

void write_u32(std::array<std::uint8_t, SAVE_IMAGE_SIZE>& bytes, std::size_t offset, std::uint32_t value) noexcept
{
    bytes[offset] = std::uint8_t(value & 0xFF);
    bytes[offset + 1] = std::uint8_t((value >> 8) & 0xFF);
    bytes[offset + 2] = std::uint8_t((value >> 16) & 0xFF);
    bytes[offset + 3] = std::uint8_t((value >> 24) & 0xFF);
}

[[nodiscard]] std::uint16_t read_u16(const std::array<std::uint8_t, SAVE_IMAGE_SIZE>& bytes, std::size_t offset) noexcept
{
    return std::uint16_t(bytes[offset]) | (std::uint16_t(bytes[offset + 1]) << 8);
}

[[nodiscard]] std::uint32_t read_u32(const std::array<std::uint8_t, SAVE_IMAGE_SIZE>& bytes, std::size_t offset) noexcept
{
    return std::uint32_t(bytes[offset]) |
           (std::uint32_t(bytes[offset + 1]) << 8) |
           (std::uint32_t(bytes[offset + 2]) << 16) |
           (std::uint32_t(bytes[offset + 3]) << 24);
}

[[nodiscard]] std::uint32_t crc32(const std::uint8_t* data, std::size_t size) noexcept
{
    std::uint32_t crc = 0xFFFFFFFFu;
    for(std::size_t index = 0; index < size; ++index)
    {
        crc ^= data[index];
        for(int bit = 0; bit < 8; ++bit)
        {
            const std::uint32_t mask = 0u - (crc & 1u);
            crc = (crc >> 1) ^ (0xEDB88320u & mask);
        }
    }
    return crc ^ 0xFFFFFFFFu;
}

template<std::size_t Size>
[[nodiscard]] std::uint8_t bool_mask(const std::array<bool, Size>& values) noexcept
{
    std::uint8_t result = 0;
    for(std::size_t index = 0; index < Size && index < 8; ++index)
    {
        if(values[index])
        {
            result |= std::uint8_t(1u << index);
        }
    }
    return result;
}

template<std::size_t Size>
void set_bool_mask(std::array<bool, Size>& values, std::uint8_t mask) noexcept
{
    for(std::size_t index = 0; index < Size; ++index)
    {
        values[index] = (mask & std::uint8_t(1u << index)) != 0;
    }
}

[[nodiscard]] ProgressState sanitize(ProgressState progress) noexcept
{
    if(progress.sound != 0 && progress.sound != 1)
    {
        progress.sound = 1;
    }
    progress.money = std::clamp(progress.money, 0, 999);

    progress.bait_owned[0] = true;
    progress.rod_owned[0] = true;
    progress.character_owned[0] = true;
    progress.character_owned[1] = true;

    if(progress.current_character < 0 || progress.current_character >= int(progress.character_owned.size()) ||
       ! progress.character_owned[progress.current_character])
    {
        progress.current_character = 0;
    }
    if(progress.current_rod < 0 || progress.current_rod >= int(progress.rod_owned.size()) ||
       ! progress.rod_owned[progress.current_rod])
    {
        progress.current_rod = 0;
    }
    if(progress.equipped_bait < 0 || progress.equipped_bait >= int(progress.bait_owned.size()) ||
       ! progress.bait_owned[progress.equipped_bait])
    {
        progress.equipped_bait = 0;
    }

    return progress;
}

}

ProgressState canonical_default_progress() noexcept
{
    return ProgressState{};
}

SaveImage encode_save(const ProgressState& source) noexcept
{
    const ProgressState progress = sanitize(source);
    SaveImage image;
    auto& bytes = image.bytes;

    bytes[0] = MAGIC[0];
    bytes[1] = MAGIC[1];
    bytes[2] = MAGIC[2];
    bytes[3] = MAGIC[3];
    write_u16(bytes, 4, SAVE_FORMAT_VERSION);
    write_u16(bytes, 6, SAVE_PAYLOAD_SIZE);

    const std::size_t p = HEADER_SIZE;
    bytes[p + 0] = std::uint8_t(progress.sound);
    bytes[p + 1] = progress.prologue_complete ? 1 : 0;
    write_u16(bytes, p + 2, std::uint16_t(progress.money));
    bytes[p + 4] = std::uint8_t(progress.current_character);
    bytes[p + 5] = std::uint8_t(progress.current_rod);
    bytes[p + 6] = std::uint8_t(progress.equipped_bait);
    bytes[p + 7] = bool_mask(progress.bait_owned);
    bytes[p + 8] = bool_mask(progress.rod_owned);
    bytes[p + 9] = bool_mask(progress.character_owned);
    bytes[p + 10] = std::uint8_t((progress.club_card ? 1u : 0u) |
                                 (progress.old_boat ? 2u : 0u) |
                                 (progress.ancient_map ? 4u : 0u) |
                                 (progress.catalog ? 8u : 0u));

    for(int fish = 0; fish < 44; ++fish)
    {
        if(progress.fish_catalog[fish])
        {
            bytes[p + 11 + (fish / 8)] |= std::uint8_t(1u << (fish % 8));
        }
    }
    // p+17 and p+18 are reserved and remain zero.

    const std::uint32_t checksum = crc32(bytes.data() + HEADER_SIZE, SAVE_PAYLOAD_SIZE);
    write_u32(bytes, 8, checksum);
    return image;
}

SaveDecodeResult decode_save(const SaveImage& image) noexcept
{
    SaveDecodeResult result;
    result.progress = canonical_default_progress();
    const auto& bytes = image.bytes;

    if(bytes[0] != MAGIC[0] || bytes[1] != MAGIC[1] || bytes[2] != MAGIC[2] || bytes[3] != MAGIC[3])
    {
        return result;
    }
    if(read_u16(bytes, 4) != SAVE_FORMAT_VERSION || read_u16(bytes, 6) != SAVE_PAYLOAD_SIZE)
    {
        return result;
    }

    const std::uint32_t expected_crc = read_u32(bytes, 8);
    const std::uint32_t actual_crc = crc32(bytes.data() + HEADER_SIZE, SAVE_PAYLOAD_SIZE);
    if(expected_crc != actual_crc)
    {
        return result;
    }

    const std::size_t p = HEADER_SIZE;
    ProgressState progress;
    progress.sound = int(bytes[p + 0]);
    progress.prologue_complete = bytes[p + 1] != 0;
    progress.money = int(read_u16(bytes, p + 2));
    progress.current_character = int(bytes[p + 4]);
    progress.current_rod = int(bytes[p + 5]);
    progress.equipped_bait = int(bytes[p + 6]);
    set_bool_mask(progress.bait_owned, bytes[p + 7]);
    set_bool_mask(progress.rod_owned, bytes[p + 8]);
    set_bool_mask(progress.character_owned, bytes[p + 9]);
    const std::uint8_t unlock_mask = bytes[p + 10];
    progress.club_card = (unlock_mask & 1u) != 0;
    progress.old_boat = (unlock_mask & 2u) != 0;
    progress.ancient_map = (unlock_mask & 4u) != 0;
    progress.catalog = (unlock_mask & 8u) != 0;
    progress.fish_catalog.fill(false);
    for(int fish = 0; fish < 44; ++fish)
    {
        progress.fish_catalog[fish] = (bytes[p + 11 + (fish / 8)] & std::uint8_t(1u << (fish % 8))) != 0;
    }

    result.valid = true;
    result.progress = sanitize(progress);
    return result;
}

}
