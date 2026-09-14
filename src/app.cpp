#include "app.h"

#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_fixed.h"
#include "bn_sprite_palettes.h"

namespace fh
{
namespace
{

int gba_channel(int value)
{
    return (value * 31 + 127) / 255;
}

}

App::App() :
    _flow(SaveStorage::load()),
    _saved_progress_revision(_flow.progress_revision())
{
    _sync_scene();
    _audio.update(_scene_state, _flow.sound_option());
    _apply_presentation();
}

void App::update()
{
    AudioCue audio_event = AudioCue::None;

    if(_transition_pending)
    {
        _presentation.update();
        if(_presentation.black_screen())
        {
            _transition_pending = false;
            _sync_scene();
            _presentation.start_fade_in();
        }
    }
    else
    {
        IntroEvent intro_event = IntroEvent::None;
        bool flash_request = false;

        switch(_scene_state)
        {
        case GameState::Title:
            if(_title_scene) { _title_scene->update(_flow); audio_event = _title_scene->take_audio_event(); }
            break;
        case GameState::Map:
            if(_map_scene) { _map_scene->update(_flow); audio_event = _map_scene->take_audio_event(); }
            break;
        case GameState::Fishing:
            if(_fishing_scene)
            {
                _fishing_scene->update(_flow);
                audio_event = _fishing_scene->take_audio_event();
                flash_request = _fishing_scene->take_flash_request();
            }
            break;
        case GameState::Shop:
            if(_shop_scene) { _shop_scene->update(_flow); audio_event = _shop_scene->take_audio_event(); }
            break;
        case GameState::Catalog:
            if(_catalog_scene) { _catalog_scene->update(_flow); audio_event = _catalog_scene->take_audio_event(); }
            break;
        case GameState::Options:
            if(_options_scene) { _options_scene->update(_flow); audio_event = _options_scene->take_audio_event(); }
            break;
        case GameState::Event:
            if(_event_scene) { _event_scene->update(_flow); audio_event = _event_scene->take_audio_event(); }
            break;
        case GameState::Intro:
            if(_intro_scene)
            {
                _intro_scene->update(_flow);
                audio_event = _intro_scene->take_audio_event();
                intro_event = _intro_scene->take_presentation_event();
            }
            break;
        }

        if(intro_event == IntroEvent::FadeInAndSound)
        {
            _presentation.start_fade_in();
        }
        else if(intro_event == IntroEvent::FadeOut)
        {
            _presentation.start_fade_out();
        }

        if(flash_request)
        {
            _presentation.start_flash();
        }

        if(_flow.state() != _scene_state)
        {
            if(_presentation.black_screen())
            {
                _sync_scene();
                _presentation.start_fade_in();
            }
            else
            {
                _presentation.start_fade_out();
                _transition_pending = true;
            }
        }

        _presentation.update();
        if(_transition_pending && _presentation.black_screen())
        {
            _transition_pending = false;
            _sync_scene();
            _presentation.start_fade_in();
        }
    }

    _apply_presentation();
    _audio.update(_scene_state, _flow.sound_option());
    _audio.play(audio_event, _flow.sound_option());

    const std::uint32_t progress_revision = _flow.progress_revision();
    if(progress_revision != _saved_progress_revision)
    {
        SaveStorage::save(_flow.progress_state());
        _saved_progress_revision = progress_revision;
    }
}

void App::_apply_presentation()
{
    const PresentationColor source = _presentation.color();
    const bn::color color(gba_channel(source.red), gba_channel(source.green), gba_channel(source.blue));
    const bn::fixed intensity = bn::fixed(_presentation.alpha()) / 255;
    bn::bg_palettes::set_fade_color(color);
    bn::sprite_palettes::set_fade_color(color);
    bn::bg_palettes::set_fade_intensity(intensity);
    bn::sprite_palettes::set_fade_intensity(intensity);
}

void App::_sync_scene()
{
    const GameState state = _flow.state();
    if(state == _scene_state)
    {
        return;
    }

    _clear_scenes();
    _scene_state = state;

    switch(state)
    {
    case GameState::Title:
        _title_scene.emplace();
        break;
    case GameState::Map:
        _map_scene.emplace();
        break;
    case GameState::Fishing:
        if(_flow.fishing_pool() >= 1 && _flow.fishing_pool() <= 5)
        {
            _fishing_scene.emplace(
                _flow.fishing_pool(), _flow.current_rod(), _flow.equipped_bait(), _flow.current_character());
        }
        break;
    case GameState::Shop:
        _shop_scene.emplace();
        break;
    case GameState::Catalog:
        _catalog_scene.emplace();
        break;
    case GameState::Options:
        _options_scene.emplace();
        break;
    case GameState::Event:
        _event_scene.emplace(_flow.event_id());
        break;
    case GameState::Intro:
        _intro_scene.emplace();
        break;
    }
}

void App::_clear_scenes()
{
    _intro_scene.reset();
    _title_scene.reset();
    _map_scene.reset();
    _fishing_scene.reset();
    _shop_scene.reset();
    _catalog_scene.reset();
    _options_scene.reset();
    _event_scene.reset();
}

}
