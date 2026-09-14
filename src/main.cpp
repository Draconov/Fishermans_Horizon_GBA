#include "bn_core.h"

#include "app.h"

int main()
{
    bn::core::init();

    fh::App app;
    while(true)
    {
        app.update();
        bn::core::update();
    }
}
