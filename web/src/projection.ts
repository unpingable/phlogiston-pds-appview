export type MembershipView = Readonly<{
  state: "active" | "not-member" | "removed" | "indeterminate";
  projection: "fresh" | "stale" | "unavailable";
  reason: string;
  reference?: string;
}>;

export interface MembershipProjection {
  membership(did: string): Promise<MembershipView>;
}

export class HttpMembershipProjection implements MembershipProjection {
  public constructor(
    readonly origin: string,
    readonly communityDid: string,
    readonly request: typeof fetch = fetch,
  ) {}

  public async membership(did: string): Promise<MembershipView> {
    const encoded = encodeURIComponent(this.communityDid);
    try {
      const response = await this.request(`${this.origin}/api/v0/communities/${encoded}/members`, {
        headers: { Accept: "application/json" },
        signal: AbortSignal.timeout(5_000),
      });
      if (!response.ok) return { state: "indeterminate", projection: "unavailable", reason: `projection_http_${response.status}` };
      const raw = await response.text();
      if (Buffer.byteLength(raw) > 256 * 1024) return { state: "indeterminate", projection: "unavailable", reason: "projection_too_large" };
      const value = JSON.parse(raw) as unknown;
      if (!isObject(value) || !Array.isArray(value.members) || !isObject(value.projection)) {
        return { state: "indeterminate", projection: "unavailable", reason: "projection_invalid" };
      }
      if (value.projection.fresh !== true) {
        return { state: "indeterminate", projection: "stale", reason: "projection_not_fresh" };
      }
      const matching = value.members.filter((item): item is Record<string, unknown> => isObject(item) && item.did === did);
      if (matching.length > 1) return { state: "indeterminate", projection: "unavailable", reason: "membership_ambiguous" };
      if (matching.length === 0) return { state: "not-member", projection: "fresh", reason: "no_authority_record" };
      const member = matching[0]!;
      const status = member.status;
      const record = isObject(member.record) && typeof member.record.uri === "string" ? member.record.uri : undefined;
      if (status === "active") return { state: "active", projection: "fresh", reason: "authority_add_projected", ...(record ? { reference: record } : {}) };
      if (status === "removed") return { state: "removed", projection: "fresh", reason: "authority_remove_projected", ...(record ? { reference: record } : {}) };
      return { state: "indeterminate", projection: "unavailable", reason: "membership_status_invalid" };
    } catch {
      return { state: "indeterminate", projection: "unavailable", reason: "projection_unavailable" };
    }
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
