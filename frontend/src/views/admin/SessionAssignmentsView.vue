<!--
  SessionAssignmentsView.vue (Admin)
  Admin can view, create, and delete session assignments. Supports CSV bulk upload (students or TAs).
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Session Assignments</h2>
        <p class="text-sm text-zinc-600 mt-1">Manage per-session rosters (students and TAs)</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButton :disabled="!selectedSessionId" @click="openAdd">Add Assignment</AppButton>
        <AppButton :disabled="!selectedSessionId" @click="showBulkUpload = true" variant="secondary"
          >Bulk Upload CSV</AppButton
        >
      </div>
    </div>

    <!-- Session Picker -->
    <div class="mb-4">
      <AppSelect v-model="selectedSessionId" label="Select Lab Session" class="max-w-md">
        <option :value="null">-- Select a session --</option>
        <option v-for="session in labSessions" :key="session.id" :value="session.id">
          {{ sessionLabel(session) }}
        </option>
      </AppSelect>
    </div>

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

    <div v-if="!selectedSessionId" class="text-zinc-500 text-sm py-8 text-center">
      Select a lab session to view and manage assignments.
    </div>

    <AppTable
      v-else
      :isEmpty="selectedSessionAssignments.length === 0"
      emptyMessage="No assignments for this session. Add users or bulk upload a roster."
    >
      <template #head>
        <th>ID</th>
        <th>Name</th>
        <th>Email</th>
        <th>Role</th>
        <th>Actions</th>
      </template>
      <tr v-for="assignment in selectedSessionAssignments" :key="assignment.id">
        <td>{{ assignment.id }}</td>
        <td>{{ getUserName(assignment.user_id) }}</td>
        <td>{{ getUserEmail(assignment.user_id) }}</td>
        <td>
          <AppBadge :variant="assignment.role === 'ta' ? 'info' : 'default'">
            {{ assignment.role }}
          </AppBadge>
        </td>
        <td>
          <AppButton variant="danger" size="sm" @click="deleteAssignmentHandler(assignment.id)"
            >Delete</AppButton
          >
        </td>
      </tr>
    </AppTable>

    <!-- Add Assignment Modal -->
    <div
      v-if="showAdd"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div
        class="bg-white p-6 rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-auto animate-in fade-in zoom-in duration-200"
      >
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-zinc-900">Add Assignment</h3>
          <button
            @click="showAdd = false"
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
        <AppCombobox
          v-model="newUserId"
          :options="userOptions"
          label="User"
          placeholder="Search by name or email..."
          required
          class="mb-3"
        />
        <AppSelect v-model="newRole" label="Role" required class="mb-3">
          <option value="student">student</option>
          <option value="ta">ta</option>
        </AppSelect>
        <p v-if="addError" class="text-sm text-red-600 mb-2">{{ addError }}</p>
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showAdd = false" variant="ghost">Cancel</AppButton>
          <AppButton @click="addAssignmentHandler">Add</AppButton>
        </div>
      </div>
    </div>

    <!-- Bulk Upload Modal -->
    <div
      v-if="showBulkUpload"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div
        class="bg-white p-6 rounded-lg shadow-xl w-full max-w-3xl max-h-[85vh] overflow-auto animate-in fade-in zoom-in duration-200"
      >
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-zinc-900">Bulk Upload Users</h3>
          <button
            @click="showBulkUpload = false"
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

        <div class="mb-3 p-2 bg-zinc-50 border border-zinc-200 rounded text-sm">
          <p class="font-medium text-zinc-700">
            Session:
            <span class="text-zinc-900">{{
              selectedSessionLabel
            }}</span>
          </p>
        </div>

        <AppSelect
          v-model="bulkRole"
          label="Assign all uploaded users as"
          :disabled="isUploading"
          class="mb-4 max-w-xs"
        >
          <option value="student">student</option>
          <option value="ta">ta</option>
        </AppSelect>

        <div class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm">
          <p class="font-semibold mb-1">CSV Format:</p>
          <p>Your CSV file should have a single column with user emails (one per row):</p>
          <ul class="list-disc list-inside mt-1">
            <li><strong>email</strong> (required): Email address of the user</li>
          </ul>
          <p class="mt-1 text-zinc-600">
            Every uploaded user is assigned with the role selected above.
          </p>
          <p class="mt-2">Example:</p>
          <code class="block mt-1 p-2 bg-white rounded">
            email<br />
            alice@university.edu<br />
            bob@university.edu
          </code>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept=".csv"
          @change="handleFileSelect"
          class="mb-4 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />

        <!-- Validation Errors -->
        <div
          v-if="validationErrors.length > 0"
          class="mb-4 p-3 bg-red-50 border border-red-200 rounded"
        >
          <p class="font-semibold text-red-800 mb-2">Validation Errors:</p>
          <ul class="text-sm text-red-700 list-disc list-inside max-h-40 overflow-auto">
            <li v-for="(error, idx) in validationErrors" :key="idx">{{ error }}</li>
          </ul>
        </div>

        <!-- Preview Table -->
        <div v-if="csvData.length > 0 && validationErrors.length === 0" class="mb-4">
          <p class="font-semibold mb-2">Preview ({{ csvData.length }} users as {{ bulkRole }}):</p>
          <div class="border rounded max-h-60 overflow-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50 sticky top-0">
                <tr>
                  <th class="px-3 py-2 text-left">Email</th>
                  <th class="px-3 py-2 text-left">Name</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in csvData" :key="idx" class="border-t">
                  <td class="px-3 py-2">{{ getUserEmail(row.user_id) }}</td>
                  <td class="px-3 py-2">{{ getUserName(row.user_id) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Progress Bar -->
        <div v-if="isUploading" class="mb-4">
          <div class="flex justify-between text-sm mb-1">
            <span>Uploading...</span>
            <span>{{ uploadProgress.current }} / {{ uploadProgress.total }}</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div
              class="bg-blue-600 h-full transition-all duration-300"
              :style="{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }"
            ></div>
          </div>
        </div>

        <!-- Upload Results -->
        <div
          v-if="uploadResults.success.length > 0 || uploadResults.errors.length > 0"
          class="mb-4"
        >
          <div
            v-if="uploadResults.success.length > 0"
            class="mb-2 p-3 bg-green-50 border border-green-200 rounded"
          >
            <p class="text-green-800 font-semibold">
              Successfully added {{ uploadResults.success.length }} users
            </p>
          </div>
          <div
            v-if="uploadResults.errors.length > 0"
            class="p-3 bg-red-50 border border-red-200 rounded"
          >
            <p class="font-semibold text-red-800 mb-2">Failed uploads:</p>
            <ul class="text-sm text-red-700 list-disc list-inside max-h-40 overflow-auto">
              <li v-for="(error, idx) in uploadResults.errors" :key="idx">{{ error }}</li>
            </ul>
          </div>
        </div>

        <div class="flex gap-2 justify-end">
          <AppButton @click="closeBulkUpload" :disabled="isUploading" variant="ghost">
            {{ isUploading ? 'Uploading...' : 'Close' }}
          </AppButton>
          <AppButton
            v-if="
              csvData.length > 0 &&
              validationErrors.length === 0 &&
              !isUploading &&
              uploadResults.success.length === 0 &&
              uploadResults.errors.length === 0
            "
            @click="startUpload"
            :disabled="isUploading"
          >
            Upload {{ csvData.length }} Users
          </AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Session Assignments view
import { ref, onMounted, computed, watch } from 'vue'
import Papa from 'papaparse'
import AppButton from '../../components/common/AppButton.vue'
import AppSelect from '../../components/common/AppSelect.vue'
import AppCombobox from '../../components/common/AppCombobox.vue'
import AppTable from '../../components/common/AppTable.vue'
import AppBadge from '../../components/common/AppBadge.vue'
import {
  getSessionAssignments,
  createSessionAssignment,
  deleteSessionAssignment,
  getLabSessions,
  getSubjects,
  getUsers,
} from '../../api/admin'
import type {
  SessionAssignment,
  SessionAssignmentCreate,
  LabSession,
  SubjectResponse,
  UserResponse,
  SubjectRole,
} from '../../types/api'
import { apiErrorMessage } from '../../utils/errors'

const assignments = ref<SessionAssignment[]>([])
const labSessions = ref<LabSession[]>([])
const subjects = ref<SubjectResponse[]>([])
const users = ref<UserResponse[]>([])
const selectedSessionId = ref<number | null>(null)
const showAdd = ref(false)
const newUserId = ref<number | null>(null)
const newRole = ref<SubjectRole>('student')
const addError = ref('')
const actionError = ref('')

// Bulk upload state
const showBulkUpload = ref(false)
const bulkRole = ref<SubjectRole>('student')
const fileInput = ref<HTMLInputElement | null>(null)
const csvData = ref<SessionAssignmentCreate[]>([])
const validationErrors = ref<string[]>([])
const isUploading = ref(false)
const uploadProgress = ref({ current: 0, total: 0 })
const uploadResults = ref<{ success: string[]; errors: string[] }>({ success: [], errors: [] })

function getSubjectName(id: number) {
  return subjects.value.find((s) => s.id === id)?.name || ''
}

function sessionLabel(session: LabSession) {
  return `${getSubjectName(session.subject_id)} — ${session.date}`
}

function getUserName(id: number) {
  return users.value.find((u) => u.id === id)?.name || ''
}

function getUserEmail(id: number) {
  return users.value.find((u) => u.id === id)?.email || ''
}

const selectedSessionLabel = computed(() => {
  if (!selectedSessionId.value) return ''
  const session = labSessions.value.find((s) => s.id === selectedSessionId.value)
  return session ? sessionLabel(session) : String(selectedSessionId.value)
})

const selectedSessionAssignments = computed(() => {
  if (!selectedSessionId.value) return []
  return assignments.value.filter((a) => a.lab_session_id === selectedSessionId.value)
})

const alreadyAssignedUserIds = computed(() => {
  return new Set(selectedSessionAssignments.value.map((a) => a.user_id))
})

const userOptions = computed(() =>
  users.value.map((u) => ({ value: u.id, label: `${u.name} (${u.email})` })),
)

async function loadBase() {
  ;[labSessions.value, subjects.value, users.value] = await Promise.all([
    getLabSessions(),
    getSubjects(),
    getUsers(),
  ])
}

async function loadAssignments() {
  if (!selectedSessionId.value) {
    assignments.value = []
    return
  }
  assignments.value = await getSessionAssignments(selectedSessionId.value)
}

onMounted(async () => {
  await loadBase()
  await loadAssignments()
})

watch(selectedSessionId, async () => {
  await loadAssignments()
})

function openAdd() {
  addError.value = ''
  showAdd.value = true
}

async function addAssignmentHandler() {
  if (!selectedSessionId.value || !newUserId.value) return
  addError.value = ''
  try {
    await createSessionAssignment({
      lab_session_id: selectedSessionId.value,
      user_id: newUserId.value,
      role: newRole.value,
    })
  } catch (e) {
    addError.value = apiErrorMessage(e)
    return
  }
  newUserId.value = null
  newRole.value = 'student'
  showAdd.value = false
  await loadAssignments()
}

async function deleteAssignmentHandler(id: number) {
  if (!confirm('Are you sure you want to remove this assignment? This action cannot be undone.')) {
    return
  }
  actionError.value = ''
  try {
    await deleteSessionAssignment(id)
  } catch (e) {
    actionError.value = apiErrorMessage(e)
    return
  }
  await loadAssignments()
}

// Bulk upload functions
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  // Reset state
  csvData.value = []
  validationErrors.value = []
  uploadResults.value = { success: [], errors: [] }

  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      validateAndLoadCSV(results.data as Record<string, string>[])
    },
    error: (error) => {
      validationErrors.value = [`CSV parsing error: ${error.message}`]
    },
  })
}

function validateAndLoadCSV(data: Record<string, string>[]) {
  const errors: string[] = []
  const validData: SessionAssignmentCreate[] = []
  const csvEmails = new Set<string>()

  if (!selectedSessionId.value) {
    errors.push('No session selected')
    validationErrors.value = errors
    return
  }

  const sessionId = selectedSessionId.value

  if (data.length === 0) {
    errors.push('CSV file is empty')
    validationErrors.value = errors
    return
  }

  data.forEach((row, index) => {
    const rowNum = index + 2 // +2 because of header row and 0-based index

    // Validate email
    if (!row.email || !row.email.trim()) {
      errors.push(`Row ${rowNum}: 'email' is required`)
      return
    }

    const email = row.email.trim().toLowerCase()

    // Basic email format validation
    if (!email.includes('@') || !email.includes('.')) {
      errors.push(`Row ${rowNum}: 'email' must be a valid email address`)
      return
    }

    // Check for duplicate emails within the CSV
    if (csvEmails.has(email)) {
      errors.push(`Row ${rowNum}: duplicate email '${row.email.trim()}' found in CSV`)
      return
    }
    csvEmails.add(email)

    // Find user by email
    const user = users.value.find((u) => u.email.toLowerCase() === email)
    if (!user) {
      errors.push(`Row ${rowNum}: user with email '${row.email.trim()}' does not exist`)
      return
    }

    // Check if already assigned to this session
    if (alreadyAssignedUserIds.value.has(user.id)) {
      errors.push(
        `Row ${rowNum}: ${user.name} is already assigned to this session`,
      )
      return
    }

    validData.push({
      lab_session_id: sessionId,
      user_id: user.id,
      role: bulkRole.value,
    })
  })

  if (errors.length > 0) {
    validationErrors.value = errors
  } else {
    csvData.value = validData
  }
}

async function startUpload() {
  if (csvData.value.length === 0) return

  isUploading.value = true
  uploadProgress.value = { current: 0, total: csvData.value.length }
  uploadResults.value = { success: [], errors: [] }

  for (const element of csvData.value) {
    const assignment = element
    const user = users.value.find((u) => u.id === assignment.user_id)
    const userName = user?.name || String(assignment.user_id)

    try {
      await createSessionAssignment({ ...assignment, role: bulkRole.value })
      uploadResults.value.success.push(`${userName} added as ${bulkRole.value}`)
      uploadProgress.value.current++
    } catch (error: unknown) {
      let errorMessage = 'Unknown error'
      if (error instanceof Error) {
        errorMessage = error.message
      } else if (typeof error === 'object' && error !== null && 'response' in error) {
        const apiError = error as { response?: { data?: { detail?: string } } }
        errorMessage = apiError.response?.data?.detail || 'Unknown error'
      }
      uploadResults.value.errors.push(`${userName}: ${errorMessage}`)
      uploadProgress.value.current++
    }
  }

  isUploading.value = false
  await loadAssignments()
}

function closeBulkUpload() {
  showBulkUpload.value = false
  bulkRole.value = 'student'
  csvData.value = []
  validationErrors.value = []
  uploadResults.value = { success: [], errors: [] }
  uploadProgress.value = { current: 0, total: 0 }
  isUploading.value = false

  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}
</script>
