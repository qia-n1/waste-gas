<template>
  <text class="status-tag" :class="normalizedType">{{ label }}</text>
</template>

<script>
export default {
  name: 'StatusTag',
  props: {
    label: {
      type: String,
      default: '--',
    },
    type: {
      type: String,
      default: 'normal',
    },
  },
  computed: {
    normalizedType() {
      const t = String(this.type || '').toLowerCase();
      if (t === 'error' || t === 'warning' || t === 'normal') return t;
      return 'normal';
    },
  },
};
</script>

