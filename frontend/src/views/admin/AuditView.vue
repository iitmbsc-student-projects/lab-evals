<!--
  AuditView.vue (Admin)
  Admin can export audit log entries as CSV with optional filters.
-->
<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Audit</h2>
        <p class="text-sm text-zinc-600 mt-1">Export the audit log for a date range and filters</p>
      </div>
    </div>

    <div class="bg-white border border-zinc-200 rounded-lg shadow-sm p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <AppInput v-model="fromDate" type="date" label="From date" required />
        <AppInput v-model="toDate" type="date" label="To date" required />
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <AppInput
          v-model="actorUserIdInput"
          type="number"
          min="1"
          step="1"
          label="Actor user ID"
          placeholder="Any actor"
        />
        <AppInput v-model="action" label="Action" placeholder="e.g. evaluation.delete" />
        <AppInput v-model="resourceType" label="Resource type" placeholder="e.g. evaluation" />
      </div>

      <p v-if="dateRangeError" class="mt-4 text-sm text-red-600">{{ dateRangeError }}</p>
      <p v-if="actorIdError" class="mt-4 text-sm text-red-600">{{ actorIdError }}</p>
      <p v-if="requestError" class="mt-4 text-sm text-red-600">{{ requestError }}</p>

      <div class="flex justify-end mt-6">
        <AppButton :disabled="!canSubmit || isDownloading" @click="onDownload">
          <AppSpinner v-if="isDownloading" size="sm" />
          <span :class="{ 'ml-2': isDownloading }">
            {{ isDownloading ? 'Downloading...' : 'Download CSV' }}
          </span>
        </AppButton>
      </div>
    </div>

    <p class="mt-4 text-sm text-zinc-500">Browse view coming in a future update.</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AppButton from '../../components/common/AppButton.vue'
import AppInput from '../../components/common/AppInput.vue'
import AppSpinner from '../../components/common/AppSpinner.vue'
import { exportAuditCsv } from '../../api/admin'

function toIsoDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const today = new Date()
const thirtyDaysAgo = new Date(today)
thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

const fromDate = ref<string>(toIsoDate(thirtyDaysAgo))
const toDate = ref<string>(toIsoDate(today))
const actorUserIdInput = ref<string>('')
const action = ref('')
const resourceType = ref('')

const isDownloading = ref(false)
const requestError = ref<string>('')

const parsedActorId = computed<number | null>(() => {
  const raw = actorUserIdInput.value
  if (raw === '' || raw === null || raw === undefined) return null
  const n = Number(raw)
  if (!Number.isFinite(n)) return NaN
  if (!Number.isInteger(n)) return NaN
  if (n < 1) return NaN
  return n
})

const actorIdError = computed(() => {
  if (actorUserIdInput.value === '') return ''
  return Number.isNaN(parsedActorId.value) ? 'Actor user ID must be a positive integer.' : ''
})

const dateRangeError = computed(() => {
  if (!fromDate.value || !toDate.value) return ''
  return toDate.value < fromDate.value ? 'To date must be on or after From date.' : ''
})

const canSubmit = computed(() => {
  if (!fromDate.value || !toDate.value) return false
  if (dateRangeError.value) return false
  if (actorIdError.value) return false
  return true
})

async function onDownload() {
  if (!canSubmit.value) return
  requestError.value = ''
  isDownloading.value = true
  try {
    const params: Parameters<typeof exportAuditCsv>[0] = {
      from_date: fromDate.value,
      to_date: toDate.value,
    }
    if (parsedActorId.value && !Number.isNaN(parsedActorId.value)) {
      params.actor_user_id = parsedActorId.value
    }
    const trimmedAction = action.value.trim()
    if (trimmedAction) params.action = trimmedAction
    const trimmedResource = resourceType.value.trim()
    if (trimmedResource) params.resource_type = trimmedResource

    await exportAuditCsv(params)
  } catch (err: unknown) {
    let message = 'Failed to download audit CSV.'
    if (err && typeof err === 'object') {
      if (
        'response' in err &&
        err.response &&
        typeof err.response === 'object' &&
        'data' in err.response
      ) {
        const data = (err as { response: { data: unknown } }).response.data
        if (data && typeof data === 'object' && 'detail' in data) {
          message = String((data as { detail: unknown }).detail)
        }
      } else if ('message' in err) {
        message = String((err as { message: unknown }).message)
      }
    }
    requestError.value = message
  } finally {
    isDownloading.value = false
  }
}
</script>
