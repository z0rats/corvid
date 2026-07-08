const STORAGE_KEY = 'otk_access_token';

export function getAccessToken() {
  return localStorage.getItem(STORAGE_KEY) || '';
}

export function setAccessToken(token) {
  localStorage.setItem(STORAGE_KEY, token);
}

export function clearAccessToken() {
  localStorage.removeItem(STORAGE_KEY);
}
