<!--
  AppAsyncSection.vue
  Wraps a section that renders fetched data: spinner while loading, error
  banner on failure, empty state when the fetch succeeded with no rows,
  otherwise the default slot. Pairs with the useAsyncTask composable.

  An error never throws away content that is already on screen. With
  `has-content`, the banner renders *above* the still-mounted default slot, so
  a failed post-mutation refresh leaves the table visible; only a first load
  that has nothing to show lets the banner stand alone. `@retry` re-runs the
  fetch from the banner.
-->
<template>
  <!--
    Always mounted, and empty until a load starts: a live region only
    announces text that lands in a region already in the DOM.
  -->
  <div class="sr-only" role="status" aria-live="polite">{{ liveMessage }}</div>

  <div v-if="loading" class="flex justify-center" :class="padClass">
    <AppSpinner size="lg" :text="loadingText || 'Loading...'" centered />
  </div>

  <template v-else>
    <div
      v-if="error"
      class="p-3 bg-red-50 border border-red-200 rounded flex items-start justify-between gap-3"
      :class="{ 'mb-4': hasContent }"
      role="alert"
    >
      <p class="text-sm text-red-700">{{ error }}</p>
      <button
        class="text-sm font-medium text-red-700 underline hover:text-red-900 shrink-0"
        @click="emit('retry')"
      >
        Retry
      </button>
    </div>

    <template v-if="!error || hasContent">
      <div
        v-if="empty"
        class="text-center bg-white rounded-xl border border-zinc-200 shadow-sm"
        :class="padClass"
      >
        <slot name="empty" />
      </div>

      <slot v-else />
    </template>
  </template>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AppSpinner from './AppSpinner.vue'

const props = defineProps<{
  loading: boolean
  error?: string
  empty?: boolean
  loadingText?: string
  // True when the slot already has something worth keeping on screen, which
  // demotes an error from "nothing to show" to a banner above the content.
  hasContent?: boolean
  // Vertical breathing room for the spinner / empty state, matching the
  // space the loaded content occupies: 'md' = py-12, 'lg' = py-16.
  spacing?: 'md' | 'lg'
}>()

const emit = defineEmits<{ retry: [] }>()

const padClass = computed(() => (props.spacing === 'lg' ? 'py-16' : 'py-12'))

// Written when a load starts, cleared when it ends.
const liveMessage = ref('')
watch(
  () => props.loading,
  (isLoading) => {
    liveMessage.value = isLoading ? props.loadingText || 'Loading...' : ''
  },
)
</script>
