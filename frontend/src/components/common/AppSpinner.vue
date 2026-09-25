<!--
  AppSpinner.vue
  Decorative loading spinner. It announces nothing on its own: the SVG is
  aria-hidden, and the live region that announces a load lives in
  AppAsyncSection (a region must be mounted before its text changes to be
  read out). Pass `label` only where the spinner is the sole indicator and
  needs a screen-reader-only name of its own.
-->
<template>
  <div :class="containerClasses">
    <svg
      :class="spinnerClasses"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      ></circle>
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
    <span v-if="text" :class="textClasses">{{ text }}</span>
    <span v-else-if="label" class="sr-only">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  size?: 'sm' | 'md' | 'lg'
  text?: string
  // Opt-in screen-reader-only label, for a spinner with no visible `text`
  // and no surrounding label of its own.
  label?: string
  centered?: boolean
}>()

const containerClasses = computed(() => {
  return props.centered ? 'flex items-center justify-center gap-2' : 'flex items-center gap-2'
})

const spinnerClasses = computed(() => {
  const base = 'animate-spin'
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-10 w-10',
  }
  return `${base} ${sizes[props.size || 'md']}`
})

const textClasses = computed(() => {
  const sizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  }
  return `text-zinc-600 ${sizes[props.size || 'md']}`
})
</script>
