const DEFAULT_BASE_URL = 'http://127.0.0.1:8002/api/v1';
const AUTH_TOKEN_KEY = 'authToken';
const AUTH_USER_KEY = 'authUser';

function getStorageValue(key) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.getStorageSync === 'function') {
      return uni.getStorageSync(key) || '';
    }
  } catch {
    // Fall back to localStorage below.
  }

  try {
    return localStorage.getItem(key) || '';
  } catch {
    return '';
  }
}

function setStorageValue(key, value) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.setStorageSync === 'function') {
      uni.setStorageSync(key, value);
      return;
    }
  } catch {
    // Fall back to localStorage below.
  }

  try {
    localStorage.setItem(key, value);
  } catch {
    // Ignore storage failures in constrained environments.
  }
}

function removeStorageValue(key) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.removeStorageSync === 'function') {
      uni.removeStorageSync(key);
      return;
    }
  } catch {
    // Fall back to localStorage below.
  }

  try {
    localStorage.removeItem(key);
  } catch {
    // Ignore storage failures in constrained environments.
  }
}

export function getBaseUrl() {
  const custom = uni.getStorageSync('apiBaseUrl');
  return custom || DEFAULT_BASE_URL;
}

export function setBaseUrl(baseUrl) {
  uni.setStorageSync('apiBaseUrl', baseUrl);
}

export function getAuthToken() {
  return getStorageValue(AUTH_TOKEN_KEY);
}

export function getAuthUser() {
  const raw = getStorageValue(AUTH_USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

export function setAuthState({ token, user }) {
  if (token) {
    setStorageValue(AUTH_TOKEN_KEY, token);
  }

  if (user) {
    setStorageValue(AUTH_USER_KEY, JSON.stringify(user));
  }
}

export function clearAuthState() {
  removeStorageValue(AUTH_TOKEN_KEY);
  removeStorageValue(AUTH_USER_KEY);
}

export function request(options) {
  const { url, method = 'GET', data, header = {} } = options;
  const token = getAuthToken();
  const requestHeader = { ...header };

  if (token) {
    requestHeader.Authorization = `Bearer ${token}`;
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${getBaseUrl()}${url}`,
      method,
      data,
      header: requestHeader,
      success: (res) => {
        if (res.statusCode === 401) {
          clearAuthState();
          if (typeof uni.redirectTo === 'function') {
            uni.redirectTo({ url: '/auth/login' });
          }
          reject(new Error('Unauthorized'));
          return;
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }
        reject(new Error(`HTTP ${res.statusCode}`));
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
}
