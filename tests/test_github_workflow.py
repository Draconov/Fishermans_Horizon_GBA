from __future__ import annotations

from pathlib import Path
import re

import yaml


WORKFLOW = Path('.github/workflows/gba.yml')


def _text() -> str:
    assert WORKFLOW.is_file(), 'single GBA workflow is missing'
    return WORKFLOW.read_text()


def test_only_one_workflow_and_yaml_is_valid():
    files = sorted(Path('.github/workflows').glob('*.yml')) + sorted(Path('.github/workflows').glob('*.yaml'))
    assert files == [WORKFLOW]
    parsed = yaml.safe_load(_text())
    assert isinstance(parsed, dict)
    assert 'jobs' in parsed


def test_workflow_is_release_focused_and_supports_manual_builds():
    text = _text()
    assert 'workflow_dispatch:' in text
    assert re.search(r'push:\n\s+tags:\n\s+- ["\']v\*["\']', text)
    assert 'pull_request:' not in text
    assert 'publish_release:' not in text
    assert 'release_tag:' in text


def test_workflow_pins_r67_toolchain_butano_and_build_steps():
    text = _text()
    assert 'devkitpro/devkitarm:20260221' in text
    assert 'devkitpro/devkitarm:20260610' not in text
    assert re.search(r'git clone .*--branch 21\.7\.1', text)
    assert 'scripts/bootstrap_m8_toolchain.py' in text
    assert '--devkitpro /opt/devkitpro' in text
    assert '--butano "$GITHUB_WORKSPACE/../butano/butano"' in text
    assert 'python3 -m pytest -q' in text
    assert 'tests/test_audio_manager.py' in text
    assert 'tests/test_save_codec.py' in text
    assert 'tests/test_github_workflow.py' in text
    for forbidden in (
        'test_reference_apk.py',
        'test_recover_m1.py',
        'test_recover_m2.py',
        'test_recover_m3.py',
        'test_recover_m4.py',
        'test_recover_m5.py',
        'test_recover_m7.py',
        'test_recover_surface.py',
        'test_stage_reference_assets.py',
        'test_m5_visual_parity.py',
        'test_verify_m0.py',
        'test_verify_m1.py',
        'test_verify_m2.py',
        'test_verify_m3.py',
        'test_verify_m4.py',
        'test_verify_m5.py',
        'test_verify_m6.py',
        'test_verify_m7.py',
    ):
        assert forbidden not in text
    assert 'FH_REFERENCE_APK' not in text
    assert 'make' in text and 'LIBBUTANO' in text
    assert 'python3 scripts/package_rom.py' in text
    assert 'mgba-sdl' in text and 'xvfb' in text
    assert 'scripts/smoke_mgba.py' in text and '--require-available' in text


def test_every_successful_build_uploads_the_rom_artifact():
    text = _text()
    upload_index = text.index('actions/upload-artifact@v4')
    nearby = text[max(0, upload_index - 350):upload_index]
    assert 'if:' not in nearby
    assert 'name: gba-rom' in text
    assert 'dist/Fishermans_Horizon_GBA.gba\n' in text
    assert 'dist/Fishermans_Horizon_GBA.gba.sha256' in text


def test_tag_push_or_manual_release_tag_can_publish_release_with_scoped_permission():
    text = _text()
    assert "github.ref_type == 'tag'" in text
    assert "github.event_name == 'workflow_dispatch'" in text
    assert "inputs.release_tag != ''" in text
    assert re.search(r'^permissions:\n  contents: read$', text, flags=re.MULTILINE)
    release_block = text.split('\n  release:', 1)[1]
    assert re.search(r'permissions:\n      contents: write', release_block)
    assert 'actions/download-artifact@v4' in release_block
    assert 'gh release upload' in release_block
    assert 'gh release create' in release_block
    assert '--target "$GITHUB_SHA"' in release_block


def test_release_payload_is_exactly_rom_and_checksum():
    text = _text()
    assert "EXPECTED='Fishermans_Horizon_GBA.gba\\nFishermans_Horizon_GBA.gba.sha256'" in text
    assert '(cd release && sha256sum -c Fishermans_Horizon_GBA.gba.sha256)' in text


def test_readme_documents_tag_and_manual_release_paths():
    text = Path('README.md').read_text()
    assert '## M6 release hardening' in text
    assert 'devkitpro/devkitarm:20260221' in text
    assert 'git tag v' in text
    assert 'git push origin v' in text
    assert 'Run workflow' in text
    assert 'release_tag' in text
    assert 'gba-rom' in text
