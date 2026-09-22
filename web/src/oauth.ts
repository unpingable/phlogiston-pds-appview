import {
  buildAtprotoLoopbackClientMetadata,
  NodeOAuthClient,
  type NodeSavedSession,
  type NodeSavedState,
  type OAuthClientMetadataInput,
} from "@atproto/oauth-client-node";
import { join } from "node:path";
import type { AppConfig } from "./config.js";
import { loopback } from "./config.js";
import { SecretJsonFileStore } from "./storage.js";

// Identity/session enrollment only. No repo or RPC write grant is requested.
export const OAUTH_SCOPE = "atproto";

export function clientMetadata(config: AppConfig): OAuthClientMetadataInput {
  const redirect = `${config.publicUrl}/oauth/callback`;
  if (loopback(config.publicUrl)) {
    return buildAtprotoLoopbackClientMetadata({ redirect_uris: [redirect], scope: OAUTH_SCOPE });
  }
  return {
    client_id: `${config.publicUrl}/oauth-client-metadata.json`,
    client_name: "Phlogiston",
    client_uri: config.publicUrl,
    redirect_uris: [redirect],
    scope: OAUTH_SCOPE,
    grant_types: ["authorization_code", "refresh_token"],
    response_types: ["code"],
    token_endpoint_auth_method: "none",
    application_type: "web",
    dpop_bound_access_tokens: true,
  };
}

export function createOAuthClient(config: AppConfig): NodeOAuthClient {
  const directory = join(config.runtimeDirectory, "oauth");
  return new NodeOAuthClient({
    clientMetadata: clientMetadata(config),
    allowHttp: loopback(config.publicUrl),
    stateStore: new SecretJsonFileStore<NodeSavedState>(join(directory, "state")),
    sessionStore: new SecretJsonFileStore<NodeSavedSession>(join(directory, "session")),
  });
}
