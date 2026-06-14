/**
 * Authentication helpers for NeedNow AI.
 *
 * Manages JWT tokens in localStorage with type-safe access.
 * Supports token decode, expiry check, and session management.
 */

const TOKEN_KEY = "neednow_token";
const USER_KEY = "neednow_user";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TokenPayload {
  sub: string; // user_id
  exp: number; // expiry timestamp
  role?: string;
  [key: string]: unknown;
}

export interface AuthUser {
  id: string;
  name?: string;
  email?: string;
}

// ---------------------------------------------------------------------------
// Token Management
// ---------------------------------------------------------------------------

/** Get the stored JWT token */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/** Store a JWT token */
export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

/** Remove the stored token (logout) */
export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/** Check if a valid (non-expired) token exists */
export function isAuthenticated(): boolean {
  const token = getToken();
  if (!token) return false;

  const payload = decodeToken(token);
  if (!payload) return false;

  return !isTokenExpired(payload);
}

// ---------------------------------------------------------------------------
// Token Decode
// ---------------------------------------------------------------------------

/** Decode a JWT payload (no signature verification — done server-side) */
export function decodeToken(token: string): TokenPayload | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;

    const payload = parts[1];
    if (!payload) return null;

    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded) as TokenPayload;
  } catch {
    return null;
  }
}

/** Check if a token payload is expired */
export function isTokenExpired(payload: TokenPayload): boolean {
  const now = Math.floor(Date.now() / 1000);
  return payload.exp < now;
}

/** Get remaining seconds until expiry */
export function tokenExpiresIn(payload: TokenPayload): number {
  const now = Math.floor(Date.now() / 1000);
  return Math.max(0, payload.exp - now);
}

// ---------------------------------------------------------------------------
// User Management
// ---------------------------------------------------------------------------

/** Store the current user info */
export function setUser(user: AuthUser): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/** Get the stored user info */
export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

/** Get the current user ID (from token or stored user) */
export function getUserId(): string | null {
  const token = getToken();
  if (token) {
    const payload = decodeToken(token);
    if (payload) return payload.sub;
  }
  const user = getUser();
  return user?.id ?? null;
}

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

/** Full logout — clear all auth state */
export function logout(): void {
  clearToken();
  if (typeof window !== "undefined") {
    window.location.href = "/";
  }
}
