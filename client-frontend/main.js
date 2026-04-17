import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createUniShim } from './uni-shim';

const uniShim = createUniShim(router);

if (typeof window !== 'undefined') {
	window.uni = uniShim;
	window.getCurrentPages = uniShim.getCurrentPages;
}

if (typeof globalThis !== 'undefined') {
	globalThis.uni = uniShim;
	globalThis.getCurrentPages = uniShim.getCurrentPages;
}

const app = createApp(App);

// Bridge common uni-app page lifecycle hooks in Vue3 Web runtime.
app.mixin({
	mounted() {
		const route = this?.$route;
		const options = route?.query || {};

		if (typeof this.$options?.onLoad === 'function') {
			this.$options.onLoad.call(this, options);
		}

		if (typeof this.$options?.onShow === 'function') {
			this.$options.onShow.call(this);
		}

		if (typeof this.$options?.onReady === 'function') {
			this.$options.onReady.call(this);
		}
	},
	unmounted() {
		if (typeof this.$options?.onHide === 'function') {
			this.$options.onHide.call(this);
		}
	},
});

app.use(router).mount('#app');