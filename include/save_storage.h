#ifndef FH_SAVE_STORAGE_H
#define FH_SAVE_STORAGE_H

#include "flow_model.h"

namespace fh
{

class SaveStorage
{
public:
    [[nodiscard]] static ProgressState load() noexcept;
    static void save(const ProgressState& progress) noexcept;
};

}

#endif
