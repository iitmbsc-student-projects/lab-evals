<!--
  AppCombobox.vue
  Reusable searchable select (combobox) styled with Tailwind.
  Use instead of AppSelect when the list of options is long enough to need filtering.
-->
<template>
  <div ref="rootEl" class="w-full">
    <div v-if="label" class="flex items-center gap-1 mb-1">
      <label class="block text-sm font-medium text-zinc-700">{{ label }}</label>
      <span v-if="required" class="text-red-500 text-sm">*</span>
    </div>
    <div class="relative">
      <input
        ref="inputEl"
        type="text"
        role="combobox"
        autocomplete="off"
        aria-autocomplete="list"
        :aria-expanded="isOpen"
        :class="inputClasses"
        :value="isOpen ? query : selectedLabel"
        :placeholder="placeholder"
        :disabled="disabled"
        @focus="onFocus"
        @input="onInput"
        @keydown="onKeydown"
      />
      <!-- Clear / chevron icon -->
      <button
        v-if="modelValue !== null && modelValue !== '' && !disabled"
        type="button"
        aria-label="Clear selection"
        class="absolute inset-y-0 right-0 flex items-center pr-2 text-zinc-400 hover:text-zinc-600"
        @click="clearSelection"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
      <span
        v-else
        class="absolute inset-y-0 right-0 flex items-center pr-2 text-zinc-400 pointer-events-none"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </span>
      <!-- Dropdown -->
      <ul
        v-if="isOpen"
        ref="listEl"
        role="listbox"
        class="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border border-zinc-200 bg-white py-1 shadow-lg"
      >
        <li
          v-for="(option, index) in filteredOptions"
          :key="String(option.value)"
          role="option"
          :aria-selected="option.value === modelValue"
          :class="[
            'cursor-pointer px-3 py-2 text-sm',
            index === highlightedIndex ? 'bg-zinc-100' : '',
            option.value === modelValue ? 'font-medium text-zinc-900' : 'text-zinc-700',
          ]"
          @mousedown.prevent="selectOption(option)"
          @mouseenter="highlightedIndex = index"
        >
          {{ option.label }}
        </li>
        <li v-if="filteredOptions.length === 0" class="px-3 py-2 text-sm text-zinc-500">
          No results found
        </li>
      </ul>
    </div>
    <p v-if="error" class="mt-1 text-sm text-red-600">{{ error }}</p>
    <p v-if="hint && !error" class="mt-1 text-sm text-zinc-500">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface ComboboxOption {
  value: string | number
  label: string
}

const props = defineProps<{
  modelValue: string | number | null
  options: ComboboxOption[]
  label?: string
  placeholder?: string
  error?: string
  hint?: string
  required?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | number | null]
  change: []
}>()

const rootEl = ref<HTMLElement | null>(null)
const inputEl = ref<HTMLInputElement | null>(null)
const listEl = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const query = ref('')
const highlightedIndex = ref(0)

const selectedOption = computed(() => props.options.find((o) => o.value === props.modelValue))
const selectedLabel = computed(() => selectedOption.value?.label ?? '')

const filteredOptions = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.options
  return props.options.filter((o) => o.label.toLowerCase().includes(q))
})

const inputClasses = computed(() => {
  const base =
    'w-full px-3 py-2 pr-8 border rounded-md text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:bg-zinc-100 disabled:cursor-not-allowed'

  if (props.error) {
    return `${base} border-red-300 focus:border-red-500 focus:ring-red-500`
  }

  return `${base} border-zinc-300 focus:border-zinc-400 focus:ring-zinc-400`
})

function open() {
  if (props.disabled) return
  isOpen.value = true
  query.value = ''
  highlightedIndex.value = Math.max(
    filteredOptions.value.findIndex((o) => o.value === props.modelValue),
    0,
  )
}

function close() {
  isOpen.value = false
  query.value = ''
}

function onFocus() {
  open()
}

function onInput(event: Event) {
  isOpen.value = true
  query.value = (event.target as HTMLInputElement).value
  highlightedIndex.value = 0
}

function selectOption(option: ComboboxOption) {
  emit('update:modelValue', option.value)
  emit('change')
  close()
  inputEl.value?.blur()
}

function clearSelection() {
  emit('update:modelValue', null)
  emit('change')
  close()
  inputEl.value?.focus()
}

function onKeydown(event: KeyboardEvent) {
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      if (!isOpen.value) {
        open()
        return
      }
      if (filteredOptions.value.length > 0) {
        highlightedIndex.value = Math.min(
          highlightedIndex.value + 1,
          filteredOptions.value.length - 1,
        )
      }
      break
    case 'ArrowUp':
      event.preventDefault()
      highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0)
      break
    case 'Enter': {
      if (!isOpen.value) return
      event.preventDefault()
      const option = filteredOptions.value[highlightedIndex.value]
      if (option) selectOption(option)
      break
    }
    case 'Escape':
      if (isOpen.value) {
        event.preventDefault()
        close()
      }
      break
    case 'Tab':
      close()
      break
  }
}

// Keep the highlighted option scrolled into view — also on open, when the
// highlighted index may be unchanged from the previous time the list closed.
watch([highlightedIndex, isOpen], async () => {
  if (!isOpen.value) return
  await nextTick()
  const item = listEl.value?.children[highlightedIndex.value] as HTMLElement | undefined
  item?.scrollIntoView({ block: 'nearest' })
})

function onDocumentMousedown(event: MouseEvent) {
  if (isOpen.value && rootEl.value && !rootEl.value.contains(event.target as Node)) {
    close()
  }
}

onMounted(() => document.addEventListener('mousedown', onDocumentMousedown))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocumentMousedown))
</script>
