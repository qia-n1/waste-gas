const BASE_URL = 'http://127.0.0.1:8000';

export function request({ url, method = 'GET', data = {}, header = {} }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...header
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }
        const msg = res.data && res.data.detail ? res.data.detail : '请求失败';
        reject(new Error(msg));
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
}
