#ifndef FH_GAME_STATE_H
#define FH_GAME_STATE_H

namespace fh
{

enum class GameState
{
    Intro,
    Title,
    Map,
    Fishing,
    Shop,
    Catalog,
    Options,
    Event,
};

[[nodiscard]] GameState initial_game_state() noexcept;

}

#endif
