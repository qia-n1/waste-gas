const DEFAULT_BASE_URL = 'http://127.0.0.1:8002/api/v1';

export function getBaseUrl() {
  const custom = uni.getStorageSync('apiBaseUrl');
  return custom || DEFAULT_BASE_URL;
}

export function setBaseUrl(baseUrl) {
  uni.setStorageSync('apiBaseUrl', baseUrl);
}

export function request(options) {
  const { url, method = 'GET', data } = options;

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${getBaseUrl()}${url}`,
      method,
      data,
      success: (res) => {
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
