#include "flow_model.h"

namespace fh
{
namespace
{

bool valid_region(Region region) noexcept
{
    return region == Region::MariMari || region == Region::JarimPerla;
}

}

FlowModel::FlowModel(ProgressState progress) noexcept :
    _progress(progress)
{
    if(! valid_region(_progress.active_region) || (_progress.active_region == Region::JarimPerla && ! _progress.car_keys))
    {
        _progress.active_region = Region::MariMari;
    }
    _selected_map_target = region_first_target(_progress.active_region);
}

GameState FlowModel::state() const noexcept { return _state; }
int FlowModel::fishing_pool() const noexcept { return _fishing_pool; }
int FlowModel::sound_option() const noexcept { return _progress.sound; }
bool FlowModel::prologue_complete() const noexcept { return _progress.prologue_complete; }
int FlowModel::event_id() const noexcept { return _event_id; }
ProgressState FlowModel::progress_state() const noexcept { return _progress; }
std::uint32_t FlowModel::progress_revision() const noexcept { return _progress_revision; }
Region FlowModel::active_region() const noexcept { return _progress.active_region; }
ShopId FlowModel::active_shop() const noexcept { return _active_shop; }

void FlowModel::complete_intro() noexcept
{
    if(_state == GameState::Intro)
    {
        _state = GameState::Title;
    }
}

void FlowModel::handle_title_command(TitleCommand command) noexcept
{
    if(_state != GameState::Title)
    {
        return;
    }

    switch(command)
    {
    case TitleCommand::Play:
        if(_progress.prologue_complete)
        {
            _selected_map_target = region_first_target(_progress.active_region);
            _state = GameState::Map;
        }
        else
        {
            _event_id = 1;
            _state = GameState::Event;
        }
        break;
    case TitleCommand::Options:
        _state = GameState::Options;
        break;
    case TitleCommand::None:
        break;
    }
}

void FlowModel::update_title_animation() noexcept
{
    ++_title_ticks;
    switch(_title_ticks)
    {
    case 1: _title_sea_tile = 113; break;
    case 13: _title_sea_tile = 114; break;
    case 25: _title_sea_tile = 113; break;
    case 37: _title_sea_tile = 112; break;
    case 49: _title_ticks = 0; break;
    default: break;
    }
}

int FlowModel::title_sea_tile() const noexcept { return _title_sea_tile; }
int FlowModel::title_ticks() const noexcept { return _title_ticks; }

void FlowModel::handle_map_command(MapCommand command) noexcept
{
    if(_state != GameState::Map)
    {
        return;
    }

    switch(command)
    {
    case MapCommand::PreviousTarget: _select_relative_map_target(-1); break;
    case MapCommand::NextTarget: _select_relative_map_target(1); break;
    case MapCommand::Left:
    case MapCommand::Right:
    case MapCommand::Up:
    case MapCommand::Down:
        _select_spatial_map_target(command);
        break;
    case MapCommand::Confirm: _activate_selected_map_target(); break;
    case MapCommand::Back: _state = GameState::Title; break;
    case MapCommand::None: break;
    }
}

void FlowModel::open_catalog_from_map() noexcept
{
    if(_state == GameState::Map && _progress.catalog)
    {
        _state = GameState::Catalog;
    }
}

void FlowModel::handle_fishing_back() noexcept
{
    if(_state == GameState::Fishing)
    {
        _state = GameState::Map;
        _fishing_pool = 0;
    }
}

void FlowModel::handle_shop_back() noexcept
{
    if(_state == GameState::Shop)
    {
        _state = GameState::Map;
    }
}

void FlowModel::handle_options_back() noexcept
{
    if(_state == GameState::Options)
    {
        _state = GameState::Title;
    }
}

void FlowModel::handle_catalog_back(bool catalog_complete) noexcept
{
    if(_state != GameState::Catalog)
    {
        return;
    }

    if(catalog_complete && _event_id != 3)
    {
        _event_id = 2;
        _state = GameState::Event;
    }
    else
    {
        _state = GameState::Map;
    }
}

void FlowModel::toggle_sound_option() noexcept
{
    _progress.sound = _progress.sound == 0 ? 1 : 0;
    ++_progress_revision;
}

void FlowModel::begin_event_dialog(int event_id) noexcept
{
    if(_state == GameState::Event && event_id == _event_id && event_id == 2)
    {
        _event_id = 3;
    }
}

void FlowModel::complete_event() noexcept
{
    if(_state == GameState::Event)
    {
        if(! _progress.prologue_complete)
        {
            _progress.prologue_complete = true;
            _progress.active_region = Region::MariMari;
            _selected_map_target = MapTarget::CrystalLake;
            ++_progress_revision;
        }
        _state = GameState::Map;
    }
}

void FlowModel::update_map_markers() noexcept
{
    if(_map_ticks % 20 == 0)
    {
        _map_spot_a_tile = 100;
        _map_spot_b_tile = 102;
    }
    else if(_map_ticks % 10 == 0)
    {
        _map_spot_a_tile = 101;
        _map_spot_b_tile = 103;
    }
    ++_map_ticks;
}

MapTarget FlowModel::selected_map_target() const noexcept { return _selected_map_target; }

bool FlowModel::map_target_enabled(MapTarget target) const noexcept
{
    const MapTargetSpec* spec = map_target_spec(target);
    if(! spec)
    {
        return false;
    }

    switch(spec->unlock)
    {
    case MapUnlock::Always: return true;
    case MapUnlock::ClubCard: return _progress.club_card;
    case MapUnlock::OldBoat: return _progress.old_boat;
    case MapUnlock::AncientMap: return _progress.ancient_map;
    case MapUnlock::Catalog: return _progress.catalog;
    case MapUnlock::CaptainsHat: return _progress.captains_hat;
    case MapUnlock::BeachBall: return _progress.beach_ball;
    case MapUnlock::CarKeys: return _progress.car_keys;
    case MapUnlock::JarimPerlaItem1: return _progress.shop2_owned[0];
    }
    return false;
}

int FlowModel::map_spot_a_tile() const noexcept { return _map_spot_a_tile; }
int FlowModel::map_spot_b_tile() const noexcept { return _map_spot_b_tile; }
int FlowModel::money() const noexcept { return _progress.money; }
int FlowModel::current_character() const noexcept { return _progress.current_character; }
int FlowModel::current_rod() const noexcept { return _progress.current_rod; }
int FlowModel::equipped_bait() const noexcept { return _progress.equipped_bait; }

bool FlowModel::bait_owned(int bait) const noexcept
{
    return bait >= 0 && bait < int(_progress.bait_owned.size()) && _progress.bait_owned[bait];
}

bool FlowModel::rod_owned(int rod) const noexcept
{
    return rod >= 0 && rod < int(_progress.rod_owned.size()) && _progress.rod_owned[rod];
}

bool FlowModel::character_owned(int character) const noexcept
{
    return character >= 0 && character < int(_progress.character_owned.size()) && _progress.character_owned[character];
}

int FlowModel::cycle_owned_character(int direction) noexcept
{
    const int previous = _progress.current_character;
    const int count = int(_progress.character_owned.size());
    const int dir = direction < 0 ? -1 : 1;
    for(int step = 1; step <= count; ++step)
    {
        const int candidate = (_progress.current_character + dir * step + count * 2) % count;
        if(_progress.character_owned[candidate])
        {
            _progress.current_character = candidate;
            break;
        }
    }
    if(_progress.current_character != previous)
    {
        ++_progress_revision;
    }
    return _progress.current_character;
}

bool FlowModel::shop_item_owned(ShopId shop, int slot) const noexcept
{
    const ShopItemSpec* item = shop_item_spec(shop, slot);
    if(! item)
    {
        return false;
    }

    if(shop == ShopId::JarimPerla)
    {
        return slot >= 0 && slot < int(_progress.shop2_owned.size()) && _progress.shop2_owned[slot];
    }

    switch(item->effect)
    {
    case ShopEffect::Bait: return bait_owned(item->effect_value);
    case ShopEffect::Rod: return rod_owned(item->effect_value);
    case ShopEffect::OldBoat: return _progress.old_boat;
    case ShopEffect::ClubCard: return _progress.club_card;
    case ShopEffect::AncientMap: return _progress.ancient_map;
    case ShopEffect::Catalog: return _progress.catalog;
    case ShopEffect::Character: return character_owned(item->effect_value);
    case ShopEffect::CaptainsHat: return _progress.captains_hat;
    case ShopEffect::BeachBall: return _progress.beach_ball;
    case ShopEffect::CarKeys: return _progress.car_keys;
    case ShopEffect::JarimPerlaItem1: return false;
    }
    return false;
}

bool FlowModel::shop_item_locked(ShopId shop, int slot) const noexcept
{
    return shop == ShopId::MariMari && slot == 7 && ! rod_owned(1);
}

bool FlowModel::shop_item_purchasable(ShopId shop, int slot) const noexcept
{
    const ShopItemSpec* item = shop_item_spec(shop, slot);
    return item && ! shop_item_locked(shop, slot) && ! shop_item_owned(shop, slot) && _progress.money >= item->price;
}

ShopPurchaseResult FlowModel::purchase_shop_item(ShopId shop, int slot) noexcept
{
    const ShopItemSpec* item = shop_item_spec(shop, slot);
    if(! item) return ShopPurchaseResult::InvalidItem;
    if(shop_item_owned(shop, slot)) return ShopPurchaseResult::SoldOut;
    if(shop_item_locked(shop, slot)) return ShopPurchaseResult::Locked;
    if(_progress.money < item->price) return ShopPurchaseResult::InsufficientFunds;

    _progress.money -= item->price;
    if(shop == ShopId::JarimPerla)
    {
        if(slot >= 0 && slot < int(_progress.shop2_owned.size()))
        {
            _progress.shop2_owned[slot] = true;
        }
    }
    else
    {
        switch(item->effect)
        {
        case ShopEffect::Bait:
            _progress.bait_owned[item->effect_value] = true;
            break;
        case ShopEffect::Rod:
            _progress.rod_owned[item->effect_value] = true;
            _progress.current_rod = item->effect_value;
            break;
        case ShopEffect::OldBoat: _progress.old_boat = true; break;
        case ShopEffect::ClubCard: _progress.club_card = true; break;
        case ShopEffect::AncientMap: _progress.ancient_map = true; break;
        case ShopEffect::Catalog: _progress.catalog = true; break;
        case ShopEffect::Character: _progress.character_owned[item->effect_value] = true; break;
        case ShopEffect::CaptainsHat: _progress.captains_hat = true; break;
        case ShopEffect::BeachBall: _progress.beach_ball = true; break;
        case ShopEffect::CarKeys: _progress.car_keys = true; break;
        case ShopEffect::JarimPerlaItem1: break;
        }
    }
    ++_progress_revision;
    return ShopPurchaseResult::Purchased;
}

bool FlowModel::shop_item_owned(int slot) const noexcept { return shop_item_owned(ShopId::MariMari, slot); }
bool FlowModel::shop_item_locked(int slot) const noexcept { return shop_item_locked(ShopId::MariMari, slot); }
bool FlowModel::shop_item_purchasable(int slot) const noexcept { return shop_item_purchasable(ShopId::MariMari, slot); }
ShopPurchaseResult FlowModel::purchase_shop_item(int slot) noexcept { return purchase_shop_item(ShopId::MariMari, slot); }

int FlowModel::cycle_owned_bait(int direction) noexcept
{
    const int previous = _progress.equipped_bait;
    const int count = int(_progress.bait_owned.size());
    const int dir = direction < 0 ? -1 : 1;
    for(int step = 1; step <= count; ++step)
    {
        const int candidate = (_progress.equipped_bait + dir * step + count * 2) % count;
        if(_progress.bait_owned[candidate])
        {
            _progress.equipped_bait = candidate;
            break;
        }
    }
    if(_progress.equipped_bait != previous)
    {
        ++_progress_revision;
    }
    return _progress.equipped_bait;
}

bool FlowModel::catalog_has_fish(int fish_number) const noexcept
{
    return fish_number >= 1 && fish_number <= int(_progress.fish_catalog.size()) && _progress.fish_catalog[fish_number - 1];
}

void FlowModel::grant_money(int amount) noexcept
{
    if(amount <= 0 || _progress.money >= 999) return;
    _progress.money += amount;
    if(_progress.money > 999) _progress.money = 999;
    ++_progress_revision;
}

void FlowModel::apply_fishing_reward(int fish_number, int reward) noexcept
{
    if(fish_number < 1 || fish_number > int(_progress.fish_catalog.size()) || reward < 0) return;
    const int previous_money = _progress.money;
    const bool previous_catalog = _progress.fish_catalog[fish_number - 1];
    _progress.money += reward;
    if(_progress.money > 999) _progress.money = 999;
    _progress.fish_catalog[fish_number - 1] = true;
    if(_progress.money != previous_money || ! previous_catalog)
    {
        ++_progress_revision;
    }
}

void FlowModel::_select_relative_map_target(int direction) noexcept
{
    const int count = region_target_count(_progress.active_region);
    if(count <= 0) return;
    int current_index = 0;
    for(int index = 0; index < count; ++index)
    {
        if(region_target_at(_progress.active_region, index) == _selected_map_target)
        {
            current_index = index;
            break;
        }
    }
    for(int step = 0; step < count; ++step)
    {
        current_index = (current_index + direction + count) % count;
        const MapTarget candidate = region_target_at(_progress.active_region, current_index);
        if(map_target_enabled(candidate))
        {
            _selected_map_target = candidate;
            return;
        }
    }
}

void FlowModel::_select_spatial_map_target(MapCommand command) noexcept
{
    const MapTargetSpec* current = map_target_spec(_selected_map_target);
    if(! current || current->region != _progress.active_region) return;

    MapTarget candidate = MapTarget::None;
    switch(command)
    {
    case MapCommand::Left: candidate = current->left; break;
    case MapCommand::Right: candidate = current->right; break;
    case MapCommand::Up: candidate = current->up; break;
    case MapCommand::Down: candidate = current->down; break;
    default: return;
    }

    const MapTargetSpec* next = map_target_spec(candidate);
    if(next && next->region == _progress.active_region && map_target_enabled(candidate))
    {
        _selected_map_target = candidate;
    }
}

void FlowModel::_activate_selected_map_target() noexcept
{
    const MapTargetSpec* spec = map_target_spec(_selected_map_target);
    if(! spec || spec->region != _progress.active_region || ! map_target_enabled(_selected_map_target)) return;

    switch(spec->action)
    {
    case MapAction::None:
        break;
    case MapAction::Fishing:
        _fishing_pool = spec->action_value;
        _state = GameState::Fishing;
        break;
    case MapAction::Shop:
        _active_shop = static_cast<ShopId>(spec->action_value);
        _state = GameState::Shop;
        break;
    case MapAction::Travel:
    {
        const Region destination = static_cast<Region>(spec->action_value);
        if(destination != Region::MariMari && destination != Region::JarimPerla) return;
        _progress.active_region = destination;
        _selected_map_target = region_first_target(destination);
        ++_progress_revision;
        break;
    }
    case MapAction::Catalog:
        if(_progress.catalog) _state = GameState::Catalog;
        break;
    }
}

}
