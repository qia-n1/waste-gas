function normalizeUniUrl(url) {
  if (!url) return '/pages/index/index'
  const [path, queryString = ''] = String(url).split('?')
  if (!queryString) return path
  return `${path}?${queryString}`
}

function parseQuery(queryString) {
  const result = {}
  if (!queryString) return result
  const search = new URLSearchParams(queryString)
  for (const [key, value] of search.entries()) {
    result[key] = value
  }
  return result
}

function createRequestImpl() {
  return function request(options = {}) {
    const {
      url,
      method = 'GET',
      data,
      success,
      fail,
      complete,
      header = {},
    } = options

    fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...header,
      },
      body: data && method !== 'GET' ? JSON.stringify(data) : undefined,
    })
      .then(async (res) => {
        const text = await res.text()
        let payload = text
        try {
          payload = text ? JSON.parse(text) : {}
        } catch {
          // Keep raw text if response is not JSON.
        }

        success?.({ statusCode: res.status, data: payload })
        complete?.({ statusCode: res.status, data: payload })
      })
      .catch((error) => {
        fail?.(error)
        complete?.(error)
      })
  }
}

export function createUniShim(router) {
  return {
    getStorageSync(key) {
      try {
        const raw = localStorage.getItem(key)
        return raw == null ? '' : raw
      } catch {
        return ''
      }
    },

    setStorageSync(key, value) {
      localStorage.setItem(key, value)
    },

    removeStorageSync(key) {
      localStorage.removeItem(key)
    },

    clearStorageSync() {
      localStorage.clear()
    },

    request: createRequestImpl(),

    navigateTo({ url }) {
      router.push(normalizeUniUrl(url))
    },

    redirectTo({ url }) {
      router.replace(normalizeUniUrl(url))
    },

    showToast({ title = '', icon = 'none' }) {
      if (icon === 'error') {
        console.error(title)
      } else {
        console.log(title)
      }
      if (title) {
        window.alert(title)
      }
    },

    showModal({ title = '', content = '', editable = false, placeholderText = '', success }) {
      if (editable) {
        const value = window.prompt(`${title}\n${content}`.trim(), content || placeholderText || '')
        success?.({ confirm: value !== null, cancel: value === null, content: value || '' })
        return
      }

      const confirmed = window.confirm(`${title}\n${content}`.trim())
      success?.({ confirm: confirmed, cancel: !confirmed })
    },

    __parseRouteQuery(fullPath = '') {
      const queryString = fullPath.split('?')[1] || ''
      return parseQuery(queryString)
    },

    getCurrentPages() {
      const currentRoute = router.currentRoute.value
      if (!currentRoute) return []
      return [{
        route: currentRoute.path.replace(/^\//, ''),
        __route__: currentRoute.path,
        options: currentRoute.query || {},
        query: currentRoute.query || {}
      }]
    },
  }
}
