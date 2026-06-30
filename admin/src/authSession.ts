const TOKEN_KEY = "food_stock_admin_token";
const API_KEY_KEY = "food_stock_api_key";
const SESSION_KEY = "food_stock_session_id";
const USER_KEY = "food_stock_admin_user";

function decodeTokenExpiryMs(token: string): number | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(atob(normalized)) as { exp?: number };
    return typeof decoded.exp === "number" ? decoded.exp * 1000 : null;
  } catch {
    return null;
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  const token = getStoredToken();
  if (!token) return false;
  const expiresAt = decodeTokenExpiryMs(token);
  if (!expiresAt) return false;
  return Date.now() < expiresAt;
}

export function clearAuthSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(API_KEY_KEY);
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(USER_KEY);
}

export function redirectToLogin(reason?: "expired"): void {
  clearAuthSession();
  const base = import.meta.env.BASE_URL ?? "/";
  const loginPath = reason === "expired" ? `${base}login?session=expired` : `${base}login`;
  if (!window.location.pathname.endsWith("/login")) {
    window.location.assign(loginPath);
  }
}
