#include "save_storage.h"

#include "bn_sram.h"

#include "save_codec.h"

namespace fh
{

ProgressState SaveStorage::load() noexcept
{
    SaveImage image;
    bn::sram::read(image);
    return decode_save(image).progress;
}

void SaveStorage::save(const ProgressState& progress) noexcept
{
    const SaveImage image = encode_save(progress);
    bn::sram::write(image);
}

}
