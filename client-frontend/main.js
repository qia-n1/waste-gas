import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createUniShim } from './uni-shim'

const app = createApp(App)

const uniShim = createUniShim(router)
globalThis.uni = uniShim

app.mixin({
	mounted() {
		const maybeOnLoad = this.$options.onLoad
		if (typeof maybeOnLoad === 'function' && !this.__uniOnLoadCalled) {
			const query = uniShim.__parseRouteQuery(this.$route?.fullPath || '')
			maybeOnLoad.call(this, query)
			this.__uniOnLoadCalled = true
		}

		const maybeOnShow = this.$options.onShow
		if (typeof maybeOnShow === 'function') {
			maybeOnShow.call(this)
		}
	},
	watch: {
		$route() {
			const maybeOnShow = this.$options.onShow
			if (typeof maybeOnShow === 'function') {
				maybeOnShow.call(this)
			}
		},
	},
})

app.use(router)
app.mount('#app')