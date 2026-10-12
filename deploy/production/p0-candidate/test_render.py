from pathlib import Path
import importlib.util
import json
import tomllib
import shutil
import pytest

SPEC = importlib.util.spec_from_file_location("candidate_render", Path(__file__).with_name("render.py"))
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
SOURCE = Path(__file__).resolve().parents[3].parent / 'community'
DID = 'did:plc:yrdhg6whfezek67fchtrmqgu'


@pytest.fixture(autouse=True)
def retire_owned_case(tmp_path):
    yield
    shutil.rmtree(tmp_path)


def test_isolated_paused_packet_and_no_external_effect(tmp_path):
    output = tmp_path / 'packet'
    result = module.render(SOURCE, output, '/opt/phlogiston-app/8834c6f/community', DID)
    env = (output / 'community-web.env').read_text()
    daemon = (output / 'communityd.toml').read_text()
    assert 'COMMUNITY_PUBLIC_URL=https://phlogiston.app\n' in env
    assert 'PORT=3211\n' in env and 'COMMUNITY_PROFILE=p0\n' in env
    assert 'COMMUNITY_SNAPSHOT_SECRET' not in env
    assert 'COMMUNITY_DID=' + DID in env and 'COMMUNITY_MODERATOR_DID=' + DID in env
    assert 'COMMUNITY_P0_HOSTED_PDS_ORIGIN=https://phlogiston.social' in env
    assert 'COMMUNITY_P0_ALLOW_BLUESKY=true' in env
    assert 'community_pds_url = "https://phlogiston.social"' in daemon
    assert 'p0_hosted_pds_origin = "https://phlogiston.social"' in daemon
    assert 'p0_allow_bluesky = true' in daemon
    assert tomllib.loads(daemon)['p0_allow_bluesky'] is True
    assert tomllib.loads((output / 'communitywatch.toml').read_text())['p0_hosted_pds_origin'] == 'https://phlogiston.social'
    assert env.count('COMMUNITY_P0_ALLOW_BLUESKY=') == 1
    assert all((output / name).read_bytes() == b'paused\n' for name in ('p0-site-state', 'p0-admission-state'))
    assert 'web_peer_uid = 42011' in daemon and 'allowed_uid = 42013' in daemon
    assert 'p0_profile = "root_only"' in daemon and 'policy_peer_uid' not in daemon
    assert 'community-authority-p0/communityd.sock' in daemon
    assert 'PORT=3210' not in env and '8080' not in env
    assert not any('notify' in p.name or 'policy' in p.name for p in output.iterdir())
    for name in module.UNITS:
        unit = (output / name).read_text()
        assert 'User=' in unit and '-p0\n' in unit
        assert 'ConditionPathExists=!/opt/phlogiston-app/8834c6f/INSTALLING' in unit
        assert 'ConditionPathExists=/opt/phlogiston-app/8834c6f/INSTALLED.json' in unit
        assert 'MemoryMax=512M' in unit and 'TasksMax=128' in unit
        assert '/etc/atproto-community/' not in unit
    assert '/toolchain/node24/bin:' in (output / 'community-live.service').read_text()
    assert '/.venv-authority/bin/communityd-serve' in (output / 'communityd.service').read_text()
    assert '/.venv-observer/bin/communitywatch-index' in (output / 'communitywatch-index.service').read_text()
    assert '/.venv-observer/bin/communitywatch-web' in (output / 'communitywatch-web.service').read_text()
    assert 'EnvironmentFile=/etc/atproto-community-p0/community-web-secret.env' in (output / 'community-live.service').read_text()
    assert result['status'] == 'inert-not-installed'
    assert len(result['canonicalSchemaHashes']) == 8
    assert result['providerMode'] == 'exact-hosted-community-plus-bluesky-authors'
    assert json.loads((output / 'candidate.json').read_text()) == result
    with pytest.raises(FileExistsError):
        module.render(SOURCE, output, '/opt/runtime', DID)


@pytest.mark.parametrize('runtime,did,uids', [('/opt/a %n', DID, (1,2,3)),('/opt/../runtime', DID, (1,2,3)),('/opt/runtime','handle.bsky.social',(1,2,3)),('/opt/runtime',DID,(1,1,3)),('/opt/runtime',DID,(0,2,3))])
def test_invalid_boundary_inputs_leave_no_packet(tmp_path, runtime, did, uids):
    output = tmp_path / 'packet'
    with pytest.raises(ValueError):
        module.render(SOURCE, output, runtime, did, uids)
    assert not output.exists()
