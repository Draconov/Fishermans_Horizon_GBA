#ifndef FH_APP_H
#define FH_APP_H

#include <cstdint>

#include "bn_optional.h"

#include "audio_manager.h"
#include "catalog_scene.h"
#include "event_scene.h"
#include "fishing_scene.h"
#include "intro_scene.h"
#include "flow_model.h"
#include "map_scene.h"
#include "options_scene.h"
#include "save_storage.h"
#include "presentation_effects.h"
#include "shop_scene.h"
#include "title_scene.h"

namespace fh
{

class App
{
public:
    App();

    void update();

private:
    void _sync_scene();
    void _clear_scenes();
    void _apply_presentation();

    FlowModel _flow;
    AudioManager _audio;
    PresentationEffects _presentation;
    std::uint32_t _saved_progress_revision = 0;
    GameState _scene_state = GameState::Title;
    bool _transition_pending = false;
    bn::optional<IntroScene> _intro_scene;
    bn::optional<TitleScene> _title_scene;
    bn::optional<MapScene> _map_scene;
    bn::optional<FishingScene> _fishing_scene;
    bn::optional<ShopScene> _shop_scene;
    bn::optional<CatalogScene> _catalog_scene;
    bn::optional<OptionsScene> _options_scene;
    bn::optional<EventScene> _event_scene;
};

}

#endif
