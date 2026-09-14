#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNSUPPORTED_LIBC_SYMBOLS = {"strlen"}

CORE_HEADER = r'''#pragma once
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace bn {

template<class T> using optional = std::optional<T>;
template<class T> constexpr T&& move(T& value) noexcept { return static_cast<T&&>(value); }

class fixed {
public:
    constexpr fixed() = default;
    constexpr fixed(int value) : _value(double(value)) {}
    constexpr fixed(double value) : _value(value) {}
    friend constexpr fixed operator/(fixed lhs, int rhs) { return fixed(lhs._value / rhs); }
private:
    double _value = 0;
};

class color {
public:
    constexpr color() = default;
    constexpr color(int red, int green, int blue) : _r(red), _g(green), _b(blue) {}
private:
    int _r = 0;
    int _g = 0;
    int _b = 0;
};

class regular_bg_map_item {};
class regular_bg_item;

class regular_bg_ptr {
public:
    regular_bg_ptr() = delete;
    explicit regular_bg_ptr(int) {}
    void set_map(const regular_bg_map_item&, int) {}
    void set_item(const regular_bg_item&) {}
};

class regular_bg_item {
public:
    regular_bg_ptr create_bg(int, int) const { return regular_bg_ptr(0); }
    regular_bg_ptr create_bg(int, int, int) const { return regular_bg_ptr(0); }
    const regular_bg_map_item& map_item() const { static regular_bg_map_item item; return item; }
};

class sprite_tiles_item {};
class sprite_item;

class sprite_ptr {
public:
    sprite_ptr() = delete;
    explicit sprite_ptr(int) {}
    void set_tiles(const sprite_tiles_item&, int) {}
    void set_item(const sprite_item&) {}
    void set_visible(bool) {}
    void set_position(int, int) {}
    void set_y(int) {}
};

class sprite_item {
public:
    sprite_ptr create_sprite(int, int) const { return sprite_ptr(0); }
    sprite_ptr create_sprite(int, int, int) const { return sprite_ptr(0); }
    const sprite_tiles_item& tiles_item() const { static sprite_tiles_item item; return item; }
};

class music_item {
public:
    void play(fixed, bool) const {}
};

namespace music {
inline bool playing() { return false; }
inline void stop() {}
}

class sound_handle {
public:
    sound_handle() = default;
    bool active() const { return true; }
    void stop() {}
};

class sound_item {
public:
    sound_handle play() const { return sound_handle(); }
    sound_handle play(double) const { return sound_handle(); }
};

template<class T, int Capacity>
class vector {
public:
    using iterator = typename std::vector<T>::iterator;
    using const_iterator = typename std::vector<T>::const_iterator;
    vector() { _data.reserve(Capacity); }
    void push_back(const T& value) { _data.push_back(value); }
    void push_back(T&& value) { _data.push_back(std::move(value)); }
    void clear() { _data.clear(); }
    [[nodiscard]] int size() const { return int(_data.size()); }
    [[nodiscard]] constexpr int max_size() const { return Capacity; }
    T& operator[](int index) { return _data[std::size_t(index)]; }
    const T& operator[](int index) const { return _data[std::size_t(index)]; }
    iterator begin() { return _data.begin(); }
    iterator end() { return _data.end(); }
    const_iterator begin() const { return _data.begin(); }
    const_iterator end() const { return _data.end(); }
private:
    std::vector<T> _data;
};

class random {
public:
    int get_int(int limit) { return limit > 0 ? 0 : 0; }
};

namespace keypad {
inline bool a_pressed() { return false; }
inline bool a_held() { return false; }
inline bool b_pressed() { return false; }
inline bool start_pressed() { return false; }
inline bool select_pressed() { return false; }
inline bool left_pressed() { return false; }
inline bool right_pressed() { return false; }
inline bool up_pressed() { return false; }
inline bool down_pressed() { return false; }
inline bool l_pressed() { return false; }
inline bool r_pressed() { return false; }
}

namespace core {
inline void init() {}
inline void update() {}
}

namespace bg_palettes {
inline void set_fade_color(color) {}
inline void set_fade_intensity(fixed) {}
}
namespace sprite_palettes {
inline void set_fade_color(color) {}
inline void set_fade_intensity(fixed) {}
}

namespace sram {
template<class T> void read(T&) {}
template<class T> void write(const T&) {}
}

} // namespace bn
'''

CORE_HEADERS = {
    "bn_bg_palettes.h", "bn_color.h", "bn_core.h", "bn_fixed.h", "bn_keypad.h",
    "bn_music.h", "bn_optional.h", "bn_random.h", "bn_regular_bg_ptr.h", "bn_sound_handle.h",
    "bn_sprite_palettes.h", "bn_sprite_ptr.h", "bn_sram.h", "bn_vector.h",
}


def _asset_headers() -> set[str]:
    headers: set[str] = set()
    pattern = re.compile(r'#include "(bn_(?:regular_bg|sprite)_items_[^"]+\.h)"')
    for path in list((ROOT / "src").glob("*.cpp")) + list((ROOT / "include").glob("*.h")):
        headers.update(pattern.findall(path.read_text(encoding="utf-8")))
    return headers


def _asset_declaration(header: str) -> str:
    stem = header[:-2]  # strip .h
    if stem.startswith("bn_regular_bg_items_"):
        name = stem.removeprefix("bn_regular_bg_items_")
        return f'#pragma once\n#include "bn_stub.h"\nnamespace bn::regular_bg_items {{ inline const regular_bg_item {name}{{}}; }}\n'
    if stem.startswith("bn_sprite_items_"):
        name = stem.removeprefix("bn_sprite_items_")
        return f'#pragma once\n#include "bn_stub.h"\nnamespace bn::sprite_items {{ inline const sprite_item {name}{{}}; }}\n'
    if stem.startswith("bn_sound_items_"):
        name = stem.removeprefix("bn_sound_items_")
        return f'#pragma once\n#include "bn_stub.h"\nnamespace bn::sound_items {{ inline const sound_item {name}{{}}; }}\n'
    raise AssertionError(header)


def _write_shim(directory: Path) -> None:
    (directory / "bn_stub.h").write_text(CORE_HEADER, encoding="utf-8")
    for header in CORE_HEADERS:
        (directory / header).write_text('#pragma once\n#include "bn_stub.h"\n', encoding="utf-8")
    for header in sorted(_asset_headers()):
        (directory / header).write_text(_asset_declaration(header), encoding="utf-8")
    sound_names = sorted(path.stem for path in (ROOT / "audio").glob("*.wav"))
    sound_items = "".join(f" inline const sound_item {name}{{}};" for name in sound_names)
    (directory / "bn_sound_items.h").write_text(
        '#pragma once\n#include "bn_stub.h"\nnamespace bn::sound_items {' + sound_items + '}\n',
        encoding="utf-8",
    )
    music_names = sorted(path.stem for path in (ROOT / "audio").glob("*.s3m"))
    music_items = "".join(f" inline const music_item {name}{{}};" for name in music_names)
    (directory / "bn_music_items.h").write_text(
        '#pragma once\n#include "bn_stub.h"\nnamespace bn::music_items {' + music_items + '}\n',
        encoding="utf-8",
    )


def main() -> int:
    compiler = shutil.which("g++")
    if not compiler:
        print("[FAIL] host g++ unavailable", file=sys.stderr)
        return 2

    nm = shutil.which("nm")
    if not nm:
        print("[FAIL] host nm unavailable", file=sys.stderr)
        return 2

    sources = sorted((ROOT / "src").glob("*.cpp"))
    with tempfile.TemporaryDirectory(prefix="fh_m8_native_") as temp:
        shim = Path(temp)
        _write_shim(shim)
        failures = 0
        for source in sources:
            command = [
                compiler, "-std=c++20", "-fsyntax-only", "-Wall", "-Wextra", "-Werror",
                "-I", str(shim), "-I", str(ROOT / "include"), str(source),
            ]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            relative = source.relative_to(ROOT).as_posix()
            if result.returncode:
                failures += 1
                print(f"[FAIL] {relative}")
                print(result.stdout, end="")
                print(result.stderr, end="")
            else:
                print(f"[PASS] {relative}")
        if failures:
            print(f"[FAIL] {failures}/{len(sources)} native translation units", file=sys.stderr)
            return 1
        print(f"[PASS] {len(sources)} native translation units")

        symbol_failures = 0
        for source in sources:
            object_path = shim / f"{source.stem}.o"
            command = [
                compiler, "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror",
                "-I", str(shim), "-I", str(ROOT / "include"),
                "-c", str(source), "-o", str(object_path),
            ]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            relative = source.relative_to(ROOT).as_posix()
            if result.returncode:
                print(f"[FAIL] {relative}: object compile failed during symbol audit")
                print(result.stdout, end="")
                print(result.stderr, end="")
                symbol_failures += 1
                continue

            nm_result = subprocess.run([nm, "-u", str(object_path)], text=True, capture_output=True, check=False)
            if nm_result.returncode:
                print(f"[FAIL] {relative}: nm failed during symbol audit")
                print(nm_result.stdout, end="")
                print(nm_result.stderr, end="")
                symbol_failures += 1
                continue

            undefined = {
                line.split()[-1].split("@", 1)[0]
                for line in nm_result.stdout.splitlines()
                if line.split()
            }
            unsupported = sorted(undefined & UNSUPPORTED_LIBC_SYMBOLS)
            for symbol in unsupported:
                print(f"[FAIL] {relative}: unsupported libc symbol {symbol}")
                symbol_failures += 1

        if symbol_failures:
            print(f"[FAIL] {symbol_failures} unsupported libc symbol reference(s)", file=sys.stderr)
            return 1

        print("[PASS] no unsupported libc symbols")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
