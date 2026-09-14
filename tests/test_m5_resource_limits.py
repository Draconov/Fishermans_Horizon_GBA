from pathlib import Path


def test_current_graphics_are_gba_legal():
    from tools.m5_validation import validate_graphics_resources

    errors = validate_graphics_resources(Path("graphics"))
    assert errors == []


def test_scene_oam_budgets_stay_below_hardware_limit():
    from tools.m5_validation import scene_oam_budgets

    budgets = scene_oam_budgets()
    assert budgets["fishing"] <= 128
    assert budgets["catalog"] <= 128
    assert max(budgets.values()) <= 128
    assert budgets["catalog"] == 109
