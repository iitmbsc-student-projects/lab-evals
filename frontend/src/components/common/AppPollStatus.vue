<!--
  AppPollStatus.vue
  One-line staleness indicator for pages that refresh themselves in the
  background ("Updated 40s ago" / "Live updates paused"), so a user can tell
  live data from data that stopped updating (hidden tab, or a dropped session).
  Deliberately tiny and low-contrast: it must never compete with the page.
-->
<template>
  <p class="text-xs text-zinc-400 whitespace-nowrap" aria-live="off">{{ text }}</p>
</template>

<script setup lang="ts">
defineProps<{ text: string }>()
</script>
