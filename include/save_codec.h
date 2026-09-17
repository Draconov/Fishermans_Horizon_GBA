#ifndef FH_SAVE_CODEC_H
#define FH_SAVE_CODEC_H

#include <array>
#include <cstddef>
#include <cstdint>

#include "flow_model.h"

namespace fh
{

constexpr std::size_t SAVE_IMAGE_SIZE = 64;
constexpr std::uint16_t SAVE_FORMAT_VERSION = 3;
constexpr std::uint16_t SAVE_PAYLOAD_SIZE = 32;

struct SaveImage
{
    std::array<std::uint8_t, SAVE_IMAGE_SIZE> bytes = {};
};

struct SaveDecodeResult
{
    bool valid = false;
    ProgressState progress = {};
};

[[nodiscard]] ProgressState canonical_default_progress() noexcept;
[[nodiscard]] SaveImage encode_save(const ProgressState& progress) noexcept;
[[nodiscard]] SaveDecodeResult decode_save(const SaveImage& image) noexcept;

}

#endif
