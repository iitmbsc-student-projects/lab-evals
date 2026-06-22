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
      </div>
      <AppButton class="self-start sm:self-auto shrink-0" @click="showCreate = true"
        >Add Lab Session</AppButton
      >
    </div>
    <!-- Subject Filter -->
    <div class="mb-4">
      <AppSelect v-model="filterSubjectId" label="Filter by Subject" class="max-w-xs">
        <option value="">All Subjects</option>
        <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
          {{ subject.name }}
        </option>
      </AppSelect>
    </div>
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
        <td v-if="editId !== session.id">
          <AppBadge :variant="session.accepting_evaluations ? 'success' : 'default'">
            {{ session.accepting_evaluations ? 'Open' : 'Closed' }}
          </AppBadge>
        </td>
        <td v-else>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="editAccepting" class="w-4 h-4 rounded" />
            <span class="text-sm text-zinc-700">Open</span>
          </label>
        </td>
        <td>
          <div class="flex flex-wrap gap-2">
            <AppButton
              v-if="editId !== session.id"
              @click="startEdit(session)"
              variant="secondary"
              size="sm"
              >Edit</AppButton
            >
            <AppButton
              v-if="editId === session.id"
              @click="saveEdit(session.id)"
              variant="success"
              size="sm"
              >Save</AppButton
            >
            <AppButton v-if="editId === session.id" @click="cancelEdit" variant="ghost" size="sm"
              >Cancel</AppButton
            >
            <AppButton
              v-if="editId !== session.id"
              @click="toggleAccepting(session)"
              variant="secondary"
              size="sm"
            >
              {{ session.accepting_evaluations ? 'Close' : 'Open' }}
            </AppButton>
            <AppButton variant="danger" size="sm" @click="deleteSessionHandler(session.id)"
              >Delete</AppButton
            >
          </div>
        </td>
      </tr>
    </AppTable>

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
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showCreate = false" variant="ghost">Cancel</AppButton>
          <AppButton @click="createSessionHandler">Create Lab Session</AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Lab Sessions CRUD view
import { ref, onMounted, computed } from 'vue'
import AppButton from '../../components/common/AppButton.vue'
import AppSelect from '../../components/common/AppSelect.vue'
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

const sessions = ref<LabSession[]>([])
const subjects = ref<SubjectResponse[]>([])
const filterSubjectId = ref<number | string>('')
const showCreate = ref(false)
const newSubjectId = ref<number | null>(null)
const newDate = ref('')
const newAccepting = ref(false)
const editId = ref<number | null>(null)
const editDate = ref('')
const editAccepting = ref(false)

const filteredSessions = computed(() => {
  if (!filterSubjectId.value) return sessions.value
  return sessions.value.filter((s) => s.subject_id === Number(filterSubjectId.value))
})

function getSubjectName(id: number) {
  return subjects.value.find((s) => s.id === id)?.name || ''
}

async function load() {
  ;[sessions.value, subjects.value] = await Promise.all([getLabSessions(), getSubjects()])
}
onMounted(load)

async function createSessionHandler() {
  if (!newSubjectId.value || !newDate.value) return
  await createLabSession({
    subject_id: newSubjectId.value,
    date: newDate.value,
    accepting_evaluations: newAccepting.value,
  })
  newSubjectId.value = null
  newDate.value = ''
  newAccepting.value = false
  showCreate.value = false
  await load()
}

function startEdit(session: LabSession) {
  editId.value = session.id
  editDate.value = session.date
  editAccepting.value = session.accepting_evaluations
}

async function saveEdit(id: number) {
  if (!editDate.value) return
  await updateLabSession(id, { date: editDate.value, accepting_evaluations: editAccepting.value })
  editId.value = null
  editDate.value = ''
  editAccepting.value = false
  await load()
}

function cancelEdit() {
  editId.value = null
  editDate.value = ''
  editAccepting.value = false
}

async function toggleAccepting(session: LabSession) {
  await setLabSessionAccepting(session.id, !session.accepting_evaluations)
  await load()
}

async function deleteSessionHandler(id: number) {
  if (
    !confirm('Are you sure you want to delete this lab session? This action cannot be undone.')
  ) {
    return
  }
  await deleteLabSession(id)
  await load()
}
</script>
