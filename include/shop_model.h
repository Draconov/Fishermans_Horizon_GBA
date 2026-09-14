#ifndef FH_SHOP_MODEL_H
#define FH_SHOP_MODEL_H

#include "progression_content.h"

namespace fh
{

class FlowModel;

class ShopModel
{
public:
    [[nodiscard]] int selected_item() const noexcept;
    [[nodiscard]] int price() const noexcept;
    [[nodiscard]] bool sold_out(const FlowModel& flow) const noexcept;

    void next() noexcept;
    void previous() noexcept;
    void select(int slot) noexcept;
    [[nodiscard]] ShopPurchaseResult purchase(FlowModel& flow) const noexcept;

private:
    int _selected_item = 0;
};

}

#endif
