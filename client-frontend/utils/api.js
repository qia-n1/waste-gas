function computeDefaultBaseUrl() {
  // Docker demo: prefer same-origin reverse proxy (/api -> backend /api/v1)
  // Local dev: fall back to direct backend URL.
  try {
    if (typeof window !== 'undefined' && window.location && window.location.origin) {
      return `${window.location.origin}/api`;
    }
  } catch {
    // ignore
  }
  return 'http://localhost:8002/api/v1';
}

const DEFAULT_BASE_URL = computeDefaultBaseUrl();
const AUTH_TOKEN_KEY = 'authToken';
const AUTH_USER_KEY = 'authUser';
const API_BASE_URL_KEY = 'apiBaseUrl';
const API_BASE_URL_RESET_FLAG = 'apiBaseUrlResetToLocalhostV1';

function normalizeBaseUrl(baseUrl) {
  const value = String(baseUrl || '').trim();
  if (!value) {
    return DEFAULT_BASE_URL;
  }

  // 与 client-backend/run.py 端口一致；旧默认 18003 无服务时会导致连接被拒绝
  return value
    .replace('http://localhost:18003/api/v1', DEFAULT_BASE_URL)
    .replace('http://127.0.0.1:18003/api/v1', 'http://127.0.0.1:8002/api/v1')
    .replace('http://localhost:18003', 'http://localhost:8002')
    .replace('http://127.0.0.1:18003', 'http://127.0.0.1:8002');
}

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
  try {
    if (typeof uni !== 'undefined' && typeof uni.getStorageSync === 'function') {
      const custom = uni.getStorageSync(API_BASE_URL_KEY);
      return normalizeBaseUrl(custom || DEFAULT_BASE_URL);
    }
  } catch {
    // Fall back to default below
  }
  return DEFAULT_BASE_URL;
}

export function setBaseUrl(baseUrl) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.setStorageSync === 'function') {
      uni.setStorageSync(API_BASE_URL_KEY, normalizeBaseUrl(baseUrl));
    }
  } catch {
    // Ignore storage failures in constrained environments
  }
}

export function resetBaseUrlToDefaultOnce() {
  try {
    if (typeof uni === 'undefined' || typeof uni.getStorageSync !== 'function') return false;
    const hasReset = uni.getStorageSync(API_BASE_URL_RESET_FLAG);
    if (hasReset) return false;
    uni.setStorageSync(API_BASE_URL_KEY, DEFAULT_BASE_URL);
    uni.removeStorageSync('lanApiBaseUrl');
    uni.setStorageSync(API_BASE_URL_RESET_FLAG, '1');
    return true;
  } catch {
    return false;
  }
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
  const requestHeader = {
    'Content-Type': 'application/json',
    ...header
  };

  if (token) {
    requestHeader.Authorization = `Bearer ${token}`;
  }

  return new Promise((resolve, reject) => {
    const finalUrl = `${getBaseUrl()}${url}`;
    uni.request({
      url: finalUrl,
      method,
      data,
      header: requestHeader,
      success: (res) => {
        if (res.statusCode === 401) {
          clearAuthState();
          if (typeof uni.redirectTo === 'function') {
            uni.redirectTo({ url: '/pages/auth/login' });
          }
          reject(new Error('Unauthorized'));
          return;
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }

        let message = `HTTP ${res.statusCode}`;
        if (res?.data?.detail) {
          if (Array.isArray(res.data.detail)) {
            message = res.data.detail.map(item => item.msg).join('；');
          } else if (typeof res.data.detail === 'string') {
            message = res.data.detail;
          }
        } else if (res?.data?.message) {
          message = res.data.message;
        }
        reject(new Error(message));
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
}
