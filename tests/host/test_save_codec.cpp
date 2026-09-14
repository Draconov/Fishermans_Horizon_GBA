#include <cassert>
#include <cstdint>

#include "save_codec.h"

namespace
{

void assert_progress_equal(const fh::ProgressState& a, const fh::ProgressState& b)
{
    assert(a.prologue_complete == b.prologue_complete);
    assert(a.sound == b.sound);
    assert(a.club_card == b.club_card);
    assert(a.old_boat == b.old_boat);
    assert(a.ancient_map == b.ancient_map);
    assert(a.catalog == b.catalog);
    assert(a.money == b.money);
    assert(a.current_character == b.current_character);
    assert(a.current_rod == b.current_rod);
    assert(a.equipped_bait == b.equipped_bait);
    assert(a.bait_owned == b.bait_owned);
    assert(a.rod_owned == b.rod_owned);
    assert(a.character_owned == b.character_owned);
    assert(a.fish_catalog == b.fish_catalog);
}

}

int main()
{
    const fh::ProgressState defaults = fh::canonical_default_progress();
    assert(defaults.money == 10);
    assert(defaults.sound == 1);
    assert(! defaults.prologue_complete);
    assert(defaults.bait_owned[0]);
    assert(defaults.rod_owned[0]);
    assert(defaults.character_owned[0]);
    assert(defaults.character_owned[1]);

    const fh::SaveImage fresh = fh::encode_save(defaults);
    static_assert(fh::SAVE_IMAGE_SIZE == 32);
    assert(fresh.bytes[0] == 'F');
    assert(fresh.bytes[1] == 'H');
    assert(fresh.bytes[2] == 'G');
    assert(fresh.bytes[3] == 'S');
    static_assert(fh::SAVE_FORMAT_VERSION == 2);
    static_assert(fh::SAVE_PAYLOAD_SIZE == 19);
    assert(fresh.bytes[4] == 2 && fresh.bytes[5] == 0);  // version 2 LE
    assert(fresh.bytes[6] == 19 && fresh.bytes[7] == 0); // payload bytes LE

    fh::SaveImage old_v1 = fresh;
    old_v1.bytes[4] = 1;
    old_v1.bytes[5] = 0;
    assert(! fh::decode_save(old_v1).valid);

    const fh::SaveDecodeResult fresh_decoded = fh::decode_save(fresh);
    assert(fresh_decoded.valid);
    assert_progress_equal(defaults, fresh_decoded.progress);

    fh::ProgressState full = defaults;
    full.prologue_complete = true;
    full.sound = 0;
    full.club_card = true;
    full.old_boat = true;
    full.ancient_map = true;
    full.catalog = true;
    full.money = 987;
    full.current_character = 5;
    full.current_rod = 2;
    full.equipped_bait = 6;
    full.bait_owned.fill(true);
    full.rod_owned.fill(true);
    full.character_owned.fill(true);
    for(int index = 0; index < 44; ++index)
    {
        full.fish_catalog[index] = index % 3 != 1;
    }

    const fh::SaveImage full_image_a = fh::encode_save(full);
    const fh::SaveImage full_image_b = fh::encode_save(full);
    assert(full_image_a.bytes == full_image_b.bytes);
    const fh::SaveDecodeResult full_decoded = fh::decode_save(full_image_a);
    assert(full_decoded.valid);
    assert_progress_equal(full, full_decoded.progress);

    fh::SaveImage corrupt = full_image_a;
    corrupt.bytes[15] ^= 0x40;
    const fh::SaveDecodeResult corrupt_decoded = fh::decode_save(corrupt);
    assert(! corrupt_decoded.valid);
    assert_progress_equal(defaults, corrupt_decoded.progress);

    fh::SaveImage wrong_version = full_image_a;
    wrong_version.bytes[4] = 3;
    const fh::SaveDecodeResult version_decoded = fh::decode_save(wrong_version);
    assert(! version_decoded.valid);
    assert_progress_equal(defaults, version_decoded.progress);

    fh::SaveImage bad_ranges = full_image_a;
    // Payload begins at 12. Corrupt range fields then recompute CRC through the public helper path
    // by decoding a deliberately encoded out-of-range source ProgressState instead.
    fh::ProgressState invalid_source = defaults;
    invalid_source.sound = 99;
    invalid_source.money = 5000;
    invalid_source.current_character = 99;
    invalid_source.current_rod = 99;
    invalid_source.equipped_bait = 99;
    invalid_source.bait_owned.fill(false);
    invalid_source.rod_owned.fill(false);
    invalid_source.character_owned.fill(false);
    const fh::SaveDecodeResult sanitized = fh::decode_save(fh::encode_save(invalid_source));
    assert(sanitized.valid);
    assert(sanitized.progress.sound == 1);
    assert(sanitized.progress.money == 999);
    assert(sanitized.progress.bait_owned[0]);
    assert(sanitized.progress.rod_owned[0]);
    assert(sanitized.progress.character_owned[0]);
    assert(sanitized.progress.character_owned[1]);
    assert(sanitized.progress.current_character == 0);
    assert(sanitized.progress.current_rod == 0);
    assert(sanitized.progress.equipped_bait == 0);

    return 0;
}
