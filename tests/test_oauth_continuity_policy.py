"""Pure V4 timing controls; no session, timer, or network fixture is used."""

import json
from pathlib import Path
import subprocess


POLICY = Path(__file__).parents[1] / "qualification/production/oauth-continuity-policy.mjs"


def policy(expression: str) -> subprocess.CompletedProcess[str]:
    source = f'import {{ assessContinuity, assessPrerequisites }} from {json.dumps(POLICY.as_uri())};\n{expression}'
    return subprocess.run(["node", "--input-type=module", "-e", source], capture_output=True, text=True, check=False, timeout=5)


def test_iso_expiry_baseline_and_post_read_currentness_pass() -> None:
    result = policy('''console.log(JSON.stringify(assessContinuity({
      scheduledAt:"2026-09-27T00:00:00Z", ranAt:"2026-09-27T12:00:01Z", minimumElapsedSeconds:43200,
      baselineObservedAt:"2026-09-27T00:00:01Z", baselineTokenExpiresAt:"2026-09-27T01:00:00Z",
      finalTokenExpiresAt:"2026-09-27T13:00:00Z"})));''')
    assert result.returncode == 0, result.stderr
    verdict = json.loads(result.stdout)
    assert verdict["refreshProvenanceMet"] is True
    assert verdict["finalTokenCurrentAtRead"] is True


def test_short_elapsed_or_still_valid_baseline_refuses_precontact() -> None:
    result = policy('''console.log(JSON.stringify(assessPrerequisites({
      scheduledAt:"2026-09-27T00:00:00Z", at:"2026-09-27T11:59:59Z", minimumElapsedSeconds:43200,
      baselineObservedAt:"2026-09-27T00:00:01Z", baselineTokenExpiresAt:"2026-09-27T13:00:00Z"})));''')
    assert result.returncode == 0, result.stderr
    verdict = json.loads(result.stdout)
    assert verdict["elapsedRequirementMet"] is False
    assert verdict["baselineExpiresBeforeProbe"] is False


def test_numeric_expiry_is_refused_for_selected_sdk_contract() -> None:
    result = policy('''try { assessPrerequisites({scheduledAt:"2026-09-27T00:00:00Z",
      at:"2026-09-27T12:00:00Z", minimumElapsedSeconds:43200, baselineObservedAt:"2026-09-27T00:00:01Z",
      baselineTokenExpiresAt:123}); } catch (error) { console.log(error.message); process.exit(7); }''')
    assert result.returncode == 7
    assert "ISO expiry string" in result.stdout
