// 直接定义多个 _interopRequireDefault 函数，确保在小程序环境中也能正常工作
function _interopRequireDefault(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

function _interopRequireDefault2(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

function _interopRequireDefault3(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

function _interopRequireDefault4(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

function _interopRequireDefault5(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

function _interopRequireDefault6(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

function _interopRequireDefault7(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

function _interopRequireDefault8(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

function _interopRequireDefault9(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}

// 确保在全局对象中也定义这些函数
if (typeof window !== 'undefined') {
  window._interopRequireDefault = _interopRequireDefault;
  window._interopRequireDefault2 = _interopRequireDefault2;
  window._interopRequireDefault3 = _interopRequireDefault3;
  window._interopRequireDefault4 = _interopRequireDefault4;
  window._interopRequireDefault5 = _interopRequireDefault5;
  window._interopRequireDefault6 = _interopRequireDefault6;
  window._interopRequireDefault7 = _interopRequireDefault7;
  window._interopRequireDefault8 = _interopRequireDefault8;
  window._interopRequireDefault9 = _interopRequireDefault9;
}

// 确保在 global 对象中也定义这些函数
if (typeof global !== 'undefined') {
  global._interopRequireDefault = _interopRequireDefault;
  global._interopRequireDefault2 = _interopRequireDefault2;
  global._interopRequireDefault3 = _interopRequireDefault3;
  global._interopRequireDefault4 = _interopRequireDefault4;
  global._interopRequireDefault5 = _interopRequireDefault5;
  global._interopRequireDefault6 = _interopRequireDefault6;
  global._interopRequireDefault7 = _interopRequireDefault7;
  global._interopRequireDefault8 = _interopRequireDefault8;
  global._interopRequireDefault9 = _interopRequireDefault9;
}

// 确保在 self 对象中也定义这些函数
if (typeof self !== 'undefined') {
  self._interopRequireDefault = _interopRequireDefault;
  self._interopRequireDefault2 = _interopRequireDefault2;
  self._interopRequireDefault3 = _interopRequireDefault3;
  self._interopRequireDefault4 = _interopRequireDefault4;
  self._interopRequireDefault5 = _interopRequireDefault5;
  self._interopRequireDefault6 = _interopRequireDefault6;
  self._interopRequireDefault7 = _interopRequireDefault7;
  self._interopRequireDefault8 = _interopRequireDefault8;
  self._interopRequireDefault9 = _interopRequireDefault9;
}

// 确保在 globalThis 对象中也定义这些函数
if (typeof globalThis !== 'undefined') {
  globalThis._interopRequireDefault = _interopRequireDefault;
  globalThis._interopRequireDefault2 = _interopRequireDefault2;
  globalThis._interopRequireDefault3 = _interopRequireDefault3;
  globalThis._interopRequireDefault4 = _interopRequireDefault4;
  globalThis._interopRequireDefault5 = _interopRequireDefault5;
  globalThis._interopRequireDefault6 = _interopRequireDefault6;
  globalThis._interopRequireDefault7 = _interopRequireDefault7;
  globalThis._interopRequireDefault8 = _interopRequireDefault8;
  globalThis._interopRequireDefault9 = _interopRequireDefault9;
}

// 使用 require 方式导入，确保在小程序环境中也能正常工作
const Vue = _interopRequireDefault(require('vue')).default;
const App = _interopRequireDefault(require('./App.vue')).default;

// 直接在模块作用域中设置 uni 全局对象
const uniShim = {
  getStorageSync: (key) => {
    try {
      if (typeof localStorage !== 'undefined') {
        const raw = localStorage.getItem(key);
        return raw == null ? '' : raw;
      }
    } catch {
      // Ignore storage failures
    }
    return '';
  },
  setStorageSync: (key, value) => {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(key, value);
      }
    } catch {
      // Ignore storage failures
    }
  },
  removeStorageSync: (key) => {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(key);
      }
    } catch {
      // Ignore storage failures
    }
  },
  clearStorageSync: () => {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.clear();
      }
    } catch {
      // Ignore storage failures
    }
  },
  request: (options = {}) => {
    const {
      url,
      method = 'GET',
      data,
      success,
      fail,
      complete,
      header = {},
    } = options;

    if (typeof fetch !== 'undefined') {
      fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...header,
        },
        body: data && method !== 'GET' ? JSON.stringify(data) : undefined,
      })
        .then(function(res) {
          return res.text().then(function(text) {
            let payload = text;
            try {
              payload = text ? JSON.parse(text) : {};
            } catch {
              // Keep raw text if response is not JSON.
            }

            if (success) success({ statusCode: res.status, data: payload });
            if (complete) complete({ statusCode: res.status, data: payload });
          });
        })
        .catch(function(error) {
          if (fail) fail(error);
          if (complete) complete(error);
        });
    } else {
      // 在小程序环境中，使用原生的 wx.request
      if (typeof wx !== 'undefined' && wx.request) {
        wx.request({
          url,
          method,
          data,
          header,
          success,
          fail,
          complete
        });
      } else {
        if (fail) fail(new Error('No request method available'));
        if (complete) complete(new Error('No request method available'));
      }
    }
  },
  navigateTo: function({ url }) {
    console.log('Navigate to:', url);
  },
  redirectTo: function({ url }) {
    console.log('Redirect to:', url);
  },
  switchTab: function({ url }) {
    console.log('Switch tab to:', url);
  },
  showToast: function({ title = '', icon = 'none' }) {
    if (icon === 'error') {
      console.error(title);
    } else {
      console.log(title);
    }
    if (title) {
      if (typeof window !== 'undefined' && window.alert) {
        window.alert(title);
      } else if (typeof wx !== 'undefined' && wx.showToast) {
        wx.showToast({ title, icon });
      }
    }
  },
  getCurrentPages: function() {
    return [{
      route: 'pages/auth/login',
      __route__: '/pages/auth/login',
      options: {},
      query: {}
    }];
  }
};

// 尝试在不同环境中设置全局 uni 对象
try {
  if (typeof window !== 'undefined') {
    window.uni = uniShim;
    window.getCurrentPages = uniShim.getCurrentPages;
  } else if (typeof global !== 'undefined') {
    global.uni = uniShim;
    global.getCurrentPages = uniShim.getCurrentPages;
  } else if (typeof self !== 'undefined') {
    self.uni = uniShim;
    self.getCurrentPages = uniShim.getCurrentPages;
  }
} catch (e) {
  console.error('Failed to set global uni object:', e);
}

// 确保 uni 在模块作用域中也可用
try {
  if (typeof globalThis !== 'undefined') {
    globalThis.uni = uniShim;
    globalThis.getCurrentPages = uniShim.getCurrentPages;
  }
} catch (e) {
  console.error('Failed to set globalThis uni object:', e);
}

Vue.config.productionTip = false;

new Vue({
  el: '#app',
  components: { App },
  template: '<App/>'
});