function instantSeconds(value, name) {
  if (typeof value !== "string" || value === "") throw new Error(`${name} is absent`);
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new Error(`${name} is not an ISO instant`);
  return parsed / 1000;
}

function expirySeconds(value, name) {
  if (typeof value !== "string" || value === "") throw new Error(`${name} must be an ISO expiry string`);
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new Error(`${name} is not an ISO instant`);
  return parsed / 1000;
}

function checkedOccurrence({ scheduledAt, at, minimumElapsedSeconds, baselineObservedAt, baselineTokenExpiresAt }) {
  if (!Number.isInteger(minimumElapsedSeconds) || minimumElapsedSeconds < 43200) throw new Error("minimum elapsed seconds must be an integer >=43200");
  const scheduled = instantSeconds(scheduledAt, "scheduled_at");
  const current = instantSeconds(at, "current_at");
  const observed = instantSeconds(baselineObservedAt, "baseline observed_at");
  const baselineExpiry = expirySeconds(baselineTokenExpiresAt, "baseline token_expires_at");
  if (observed < scheduled || observed > current) throw new Error("baseline observation is outside the occurrence interval");
  return { scheduled, current, baselineExpiry };
}

export function assessPrerequisites(input) {
  const { scheduled, current, baselineExpiry } = checkedOccurrence(input);
  return Object.freeze({
    actualElapsedSeconds: current - scheduled,
    minimumElapsedSeconds: input.minimumElapsedSeconds,
    elapsedRequirementMet: current - scheduled >= input.minimumElapsedSeconds,
    baselineExpiresBeforeProbe: baselineExpiry <= scheduled + input.minimumElapsedSeconds,
  });
}

export function assessContinuity(input) {
  const prerequisite = assessPrerequisites({ scheduledAt: input.scheduledAt, at: input.ranAt, minimumElapsedSeconds: input.minimumElapsedSeconds, baselineObservedAt: input.baselineObservedAt, baselineTokenExpiresAt: input.baselineTokenExpiresAt });
  const finalExpiry = expirySeconds(input.finalTokenExpiresAt, "final token_expires_at");
  const ran = instantSeconds(input.ranAt, "ran_at");
  const baseline = expirySeconds(input.baselineTokenExpiresAt, "baseline token_expires_at");
  const tokenExpiryAdvanced = finalExpiry > baseline;
  const finalTokenCurrentAtRead = finalExpiry > ran;
  return Object.freeze({ ...prerequisite, tokenExpiryAdvanced, finalTokenCurrentAtRead, refreshProvenanceMet: prerequisite.baselineExpiresBeforeProbe && tokenExpiryAdvanced && finalTokenCurrentAtRead });
}
