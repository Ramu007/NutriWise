/**
 * Auth helpers — tiny shim until we wire the Cognito hosted UI.
 *
 * Right now the app has two modes:
 *   1. **Dev bypass**: set `EXPO_PUBLIC_DEV_USER_ID` and every request goes as
 *      that user via the `X-User-Id` header. The API's dev fallback accepts
 *      it when `ENV=dev` and no user pool is configured.
 *   2. **Token mode**: call `setAuthToken(jwt)` after a future Cognito login;
 *      every request thereafter sends `Authorization: Bearer <jwt>`.
 *
 * We deliberately keep this file stateless and dep-free so adding Expo
 * SecureStore later is a localized change.
 */
import { api } from './api';

const DEV_USER_ID = process.env.EXPO_PUBLIC_DEV_USER_ID ?? 'demo-user';

export function currentUserId(): string {
  // In token mode the server infers the user from the JWT `sub`. `userId` is
  // only read by the client to send `X-User-Id` for the dev fallback; the
  // server ignores it when a valid bearer token is present.
  return DEV_USER_ID;
}

export function signIn(token: string): void {
  api.setAuthToken(token);
}

export function signOut(): void {
  api.setAuthToken(null);
}
