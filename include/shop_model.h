#ifndef FH_SHOP_MODEL_H
#define FH_SHOP_MODEL_H

#include "progression_content.h"

namespace fh
{

class FlowModel;

enum class ShopCheatKey
{
    Up,
    Down,
    Left,
    Right,
    B,
    A,
};

enum class ShopCheatResult
{
    NoProgress,
    Progressed,
    Completed,
};

class ShopModel
{
public:
    [[nodiscard]] int selected_item() const noexcept;
    [[nodiscard]] int price() const noexcept;
    [[nodiscard]] bool sold_out(const FlowModel& flow) const noexcept;

    void next() noexcept;
    void previous() noexcept;
    void move_left() noexcept;
    void move_right() noexcept;
    void move_up() noexcept;
    void move_down() noexcept;
    void select(int slot) noexcept;
    [[nodiscard]] ShopPurchaseResult purchase(FlowModel& flow) const noexcept;
    [[nodiscard]] ShopCheatResult push_cheat_key(ShopCheatKey key, int frame) noexcept;
    void reset_cheat() noexcept;

private:
    int _selected_item = 0;
    int _cheat_index = 0;
    int _cheat_start_frame = 0;
};

}

#endif
