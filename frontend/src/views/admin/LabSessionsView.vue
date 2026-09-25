<!--
  LabSessionsView.vue (Admin)
  Admin can view, create, edit, delete, and toggle lab sessions.
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Lab Sessions</h2>
        <p class="text-sm text-zinc-600 mt-1">Manage lab sessions per subject</p>
        <AppPollStatus :text="pollStatus" class="mt-1" />
      </div>
      <AppButton class="self-start sm:self-auto shrink-0" @click="openCreate"
        >Add Lab Session</AppButton
      >
    </div>
    <!-- Subject Filter -->
    <div class="mb-4">
      <AppSelect
        v-model="filterSubjectId"
        label="Filter by Subject"
        class="max-w-xs"
        :disabled="loading"
      >
        <option value="">All Subjects</option>
        <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
          {{ subject.name }}
        </option>
      </AppSelect>
    </div>
    <!-- Action error banner (edit / open-close / delete) -->
    <div
      v-if="actionError"
      class="mb-4 p-3 bg-red-50 border border-red-200 rounded flex items-start justify-between gap-3"
    >
      <p class="text-sm text-red-700">{{ actionError }}</p>
      <button
        @click="actionError = ''"
        class="text-red-400 hover:text-red-600 transition-colors shrink-0"
        aria-label="Dismiss error"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    <AppAsyncSection
      :loading="loading"
      :error="loadError"
      :has-content="sessions.length > 0"
      loading-text="Loading lab sessions..."
      @retry="load()"
    >
      <AppTable
        :isEmpty="filteredSessions.length === 0"
        emptyMessage="No lab sessions found. Add your first lab session or adjust your filters."
      >
        <template #head>
          <th>ID</th>
          <th>Subject</th>
          <th>Date</th>
          <th>Status</th>
          <th>Actions</th>
        </template>
        <tr v-for="session in filteredSessions" :key="session.id">
          <td class="font-mono text-xs text-zinc-500">{{ session.id }}</td>
          <td>{{ getSubjectName(session.subject_id) }}</td>
          <td v-if="editId !== session.id">{{ session.date }}</td>
          <td v-else>
            <input
              type="date"
              v-model="editDate"
              class="w-full px-3 py-2 border border-zinc-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
            />
          </td>
          <!-- Always the live value, in edit mode too: open/closed is changed
               through its own toggle below, never carried along by a date edit. -->
          <td>
            <AppBadge :variant="session.accepting_evaluations ? 'success' : 'default'">
              {{ session.accepting_evaluations ? 'Open' : 'Closed' }}
            </AppBadge>
          </td>
          <td>
            <div class="flex flex-wrap gap-2">
              <AppButton
                v-if="editId !== session.id"
                @click="startEdit(session)"
                variant="secondary"
                size="sm"
                :disabled="rowBusy"
                >Edit</AppButton
              >
              <AppButton
                v-if="editId === session.id"
                @click="saveEdit(session.id)"
                variant="success"
                size="sm"
                :disabled="rowBusy"
                >{{ rowBusyKey === `save:${session.id}` ? 'Saving...' : 'Save' }}</AppButton
              >
              <AppButton
                v-if="editId === session.id"
                @click="cancelEdit"
                variant="ghost"
                size="sm"
                :disabled="rowBusy"
                >Cancel</AppButton
              >
              <AppButton
                v-if="editId !== session.id"
                @click="toggleAccepting(session)"
                variant="secondary"
                size="sm"
                :disabled="rowBusy"
              >
                <template v-if="rowBusyKey === `toggle:${session.id}`">
                  {{ session.accepting_evaluations ? 'Closing...' : 'Opening...' }}
                </template>
                <template v-else>
                  {{ session.accepting_evaluations ? 'Close' : 'Open' }}
                </template>
              </AppButton>
              <AppButton
                variant="danger"
                size="sm"
                :disabled="rowBusy"
                @click="deleteSessionHandler(session.id)"
                >{{ rowBusyKey === `delete:${session.id}` ? 'Deleting...' : 'Delete' }}</AppButton
              >
            </div>
          </td>
        </tr>
      </AppTable>
    </AppAsyncSection>

    <!-- Create Modal -->
    <div
      v-if="showCreate"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div
        class="bg-white p-6 rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-auto animate-in fade-in zoom-in duration-200"
      >
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-zinc-900">Add Lab Session</h3>
          <button
            @click="showCreate = false"
            class="text-zinc-400 hover:text-zinc-600 transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <AppSelect v-model="newSubjectId" label="Subject" required class="mb-3">
          <option :value="null" disabled>Select a subject</option>
          <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
            {{ subject.name }}
          </option>
        </AppSelect>
        <div class="mb-3">
          <label class="block text-sm font-medium text-zinc-700 mb-1">
            Date <span class="text-red-500">*</span>
          </label>
          <input
            type="date"
            v-model="newDate"
            class="w-full px-3 py-2 border border-zinc-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </div>
        <label class="flex items-center gap-2 cursor-pointer mb-4">
          <input type="checkbox" v-model="newAccepting" class="w-4 h-4 rounded" />
          <span class="text-sm font-medium text-zinc-700">Open for evaluations</span>
        </label>
        <p v-if="createError" class="text-sm text-red-600 mb-2">{{ createError }}</p>
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showCreate = false" variant="ghost" :disabled="creating"
            >Cancel</AppButton
          >
          <AppButton @click="createSessionHandler" :disabled="creating">{{
            creating ? 'Creating...' : 'Create Lab Session'
          }}</AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Lab Sessions CRUD view
import { ref, computed } from 'vue'
import AppButton from '../../components/common/AppButton.vue'
import AppSelect from '../../components/common/AppSelect.vue'
import AppAsyncSection from '../../components/common/AppAsyncSection.vue'
import AppTable from '../../components/common/AppTable.vue'
import AppBadge from '../../components/common/AppBadge.vue'
import {
  getLabSessions,
  createLabSession,
  updateLabSession,
  deleteLabSession,
  setLabSessionAccepting,
  getSubjects,
} from '../../api/admin'
import type { LabSession, SubjectResponse } from '../../types/api'
import { useAsyncAction, useAsyncTask } from '../../composables/useAsync'
import { usePolling, type PollContext } from '../../composables/usePolling'
import AppPollStatus from '../../components/common/AppPollStatus.vue'

const sessions = ref<LabSession[]>([])
const subjects = ref<SubjectResponse[]>([])
const filterSubjectId = ref<number | string>('')
const showCreate = ref(false)
const newSubjectId = ref<number | null>(null)
const newDate = ref('')
const newAccepting = ref(false)
const editId = ref<number | null>(null)
const editDate = ref('')

const filteredSessions = computed(() => {
  if (!filterSubjectId.value) return sessions.value
  return sessions.value.filter((s) => s.subject_id === Number(filterSubjectId.value))
})

function getSubjectName(id: number) {
  return subjects.value.find((s) => s.id === id)?.name || ''
}

async function loadSessions(ctx?: PollContext) {
  const [s, sub] = await Promise.all([getLabSessions(undefined, ctx?.signal), getSubjects()])
  if (ctx?.isStale()) return
  sessions.value = s
  subjects.value = sub
}

const {
  loading,
  error: loadError,
  run: load,
  refresh,
} = useAsyncTask(() => loadSessions(), { immediate: true })

// `accepting_evaluations` gates whether TAs can grade at all, and more than
// one admin may be working during a lab, so a stale Open/Closed badge here is
// worth correcting. Suspended while a create modal or an inline edit row is
// open, so a refresh cannot swap the table out from under it.
//
// Polls the raw loader, not the task's refresh(): a failed background tick is
// swallowed rather than replacing the table with an error.
const { statusText: pollStatus, invalidate: invalidatePoll } = usePolling(loadSessions, {
  paused: () => showCreate.value || editId.value !== null,
})

// Create is its own in-flight state (the modal button); the row actions
// (edit / open-close / delete) share one, as only one can run at a time.
const { busy: creating, error: createError, run: runCreate } = useAsyncAction()
const {
  busy: rowBusy,
  busyKey: rowBusyKey,
  error: actionError,
  run: runRowAction,
} = useAsyncAction()

function openCreate() {
  createError.value = ''
  showCreate.value = true
}

async function createSessionHandler() {
  invalidatePoll()
  const subjectId = newSubjectId.value
  if (!subjectId || !newDate.value) return
  await runCreate(async () => {
    await createLabSession({
      subject_id: subjectId,
      date: newDate.value,
      accepting_evaluations: newAccepting.value,
    })
    newSubjectId.value = null
    newDate.value = ''
    newAccepting.value = false
    showCreate.value = false
  })
  // Silent: the table stays on screen instead of collapsing into a spinner.
  if (!createError.value) await refresh()
}

function startEdit(session: LabSession) {
  editId.value = session.id
  editDate.value = session.date
}

async function saveEdit(id: number) {
  invalidatePoll()
  if (!editDate.value) return
  await runRowAction(async () => {
    // Date only. Sending `accepting_evaluations` here would overwrite it with
    // the value captured at startEdit, silently re-opening a session another
    // admin closed in the meantime.
    await updateLabSession(id, { date: editDate.value })
    editId.value = null
    editDate.value = ''
  }, `save:${id}`)
  if (!actionError.value) await refresh()
}

function cancelEdit() {
  editId.value = null
  editDate.value = ''
}

async function toggleAccepting(session: LabSession) {
  invalidatePoll()
  await runRowAction(async () => {
    await setLabSessionAccepting(session.id, !session.accepting_evaluations)
  }, `toggle:${session.id}`)
  if (!actionError.value) await refresh()
}

async function deleteSessionHandler(id: number) {
  invalidatePoll()
  if (
    !confirm('Are you sure you want to delete this lab session? This action cannot be undone.')
  ) {
    return
  }
  await runRowAction(async () => {
    await deleteLabSession(id)
  }, `delete:${id}`)
  if (!actionError.value) await refresh()
}
</script>
