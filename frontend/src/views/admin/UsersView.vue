<!--
  UsersView.vue (Admin)
  Admin can view, create, edit, and delete users.
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Users</h2>
        <p class="text-sm text-zinc-600 mt-1">Manage users and bulk upload via CSV</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButton @click="showCreate = true">Add User</AppButton>
        <AppButton @click="showBulkUpload = true" variant="secondary">Bulk Upload CSV</AppButton>
      </div>
    </div>
    <AppTable
      :isEmpty="users.length === 0"
      emptyMessage="No users found. Add your first user or use bulk upload."
    >
      <template #head>
        <th>ID</th>
        <th>Name</th>
        <th>Email</th>
        <th>Admin?</th>
        <th>Actions</th>
      </template>
      <tr v-for="user in users" :key="user.id">
        <td>{{ user.id }}</td>
        <td v-if="editId !== user.id">{{ user.name }}</td>
        <td v-else>
          <AppInput v-model="editName" />
        </td>
        <td v-if="editId !== user.id">{{ user.email }}</td>
        <td v-else>
          <AppInput v-model="editEmail" />
        </td>
        <td v-if="editId !== user.id">
          <AppBadge :variant="user.is_admin ? 'purple' : 'default'">
            {{ user.is_admin ? 'Yes' : 'No' }}
          </AppBadge>
        </td>
        <td v-else>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="editIsAdmin" class="w-4 h-4 rounded" />
            <span class="text-sm text-zinc-700">Admin</span>
          </label>
        </td>
        <td>
          <div class="flex gap-2">
            <AppButton
              v-if="editId !== user.id"
              @click="startEdit(user)"
              variant="secondary"
              size="sm"
              >Edit</AppButton
            >
            <AppButton
              v-if="editId === user.id"
              @click="saveEdit(user.id)"
              variant="success"
              size="sm"
              >Save</AppButton
            >
            <AppButton v-if="editId === user.id" @click="cancelEdit" variant="ghost" size="sm"
              >Cancel</AppButton
            >
            <AppButton variant="danger" size="sm" @click="deleteUserHandler(user.id)"
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
          <h3 class="text-lg font-semibold text-zinc-900">Add User</h3>
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
        <AppInput v-model="newName" placeholder="Name" label="Name" required class="mb-3" />
        <AppInput v-model="newEmail" placeholder="Email" label="Email" required class="mb-3" />
        <label class="flex items-center gap-2 cursor-pointer mb-4">
          <input type="checkbox" v-model="newIsAdmin" class="w-4 h-4 rounded" />
          <span class="text-sm font-medium text-zinc-700">Admin user</span>
        </label>
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showCreate = false" variant="ghost">Cancel</AppButton>
          <AppButton @click="createUserHandler">Create User</AppButton>
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

        <div class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm">
          <p class="font-semibold mb-1">CSV Format:</p>
          <p>Your CSV file should have the following columns:</p>
          <ul class="list-disc list-inside mt-1">
            <li><strong>name</strong> (required): User's full name</li>
            <li><strong>email</strong> (required): User's email address (must be unique)</li>
          </ul>
          <p class="mt-1 text-zinc-600">Users are created as non-admin by default.</p>
          <p class="mt-2">Example:</p>
          <code class="block mt-1 p-2 bg-white rounded">
            name,email<br />
            John Doe,john@example.com<br />
            Jane Smith,jane@example.com
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

        <!-- Skipped rows notice (shown in preview stage) -->
        <div
          v-if="skippedCount > 0 && uploadResults.success.length === 0 && uploadResults.errors.length === 0"
          class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800"
        >
          <span class="font-semibold">{{ skippedCount }} row{{ skippedCount === 1 ? '' : 's' }} skipped</span>
          — {{ skippedCount === 1 ? 'that email already exists' : 'those emails already exist' }} in the system and will not be re-added.
        </div>

        <!-- Preview Table -->
        <div v-if="csvData.length > 0 && validationErrors.length === 0" class="mb-4">
          <p class="font-semibold mb-2">Preview ({{ csvData.length }} user{{ csvData.length === 1 ? '' : 's' }} to add<span v-if="skippedCount > 0">, {{ skippedCount }} skipped</span>):</p>
          <div class="border rounded max-h-60 overflow-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50 sticky top-0">
                <tr>
                  <th class="px-3 py-2 text-left">Name</th>
                  <th class="px-3 py-2 text-left">Email</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in csvData" :key="idx" class="border-t">
                  <td class="px-3 py-2">{{ row.name }}</td>
                  <td class="px-3 py-2">{{ row.email }}</td>
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
          v-if="uploadResults.success.length > 0 || uploadResults.skipped > 0 || uploadResults.errors.length > 0"
          class="mb-4"
        >
          <div
            v-if="uploadResults.success.length > 0"
            class="mb-2 p-3 bg-green-50 border border-green-200 rounded"
          >
            <p class="text-green-800 font-semibold">
              Successfully added {{ uploadResults.success.length }} user{{ uploadResults.success.length === 1 ? '' : 's' }}
            </p>
          </div>
          <div
            v-if="uploadResults.skipped > 0"
            class="mb-2 p-3 bg-yellow-50 border border-yellow-200 rounded"
          >
            <p class="text-yellow-800 font-semibold">
              {{ uploadResults.skipped }} row{{ uploadResults.skipped === 1 ? '' : 's' }} skipped (already exist{{ uploadResults.skipped === 1 ? 's' : '' }} in the system)
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
            Upload {{ csvData.length }} User{{ csvData.length === 1 ? '' : 's' }}<span v-if="skippedCount > 0"> ({{ skippedCount }} skipped)</span>
          </AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Users CRUD view
import { ref, onMounted } from 'vue'
import Papa from 'papaparse'
import AppButton from '../../components/common/AppButton.vue'
import AppInput from '../../components/common/AppInput.vue'
import AppBadge from '../../components/common/AppBadge.vue'
import AppTable from '../../components/common/AppTable.vue'
import { getUsers, createUser, updateUser, deleteUser } from '../../api/admin'
import type { UserResponse, UserCreate } from '../../types/api'

const users = ref<UserResponse[]>([])
const showCreate = ref(false)
const newName = ref('')
const newEmail = ref('')
const newIsAdmin = ref(false)
const editId = ref<number | null>(null)
const editName = ref('')
const editEmail = ref('')
const editIsAdmin = ref(false)

// Bulk upload state
const showBulkUpload = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const csvData = ref<UserCreate[]>([])
const validationErrors = ref<string[]>([])
const skippedCount = ref(0)
const isUploading = ref(false)
const uploadProgress = ref({ current: 0, total: 0 })
const uploadResults = ref<{ success: string[]; skipped: number; errors: string[] }>({
  success: [],
  skipped: 0,
  errors: [],
})

async function load() {
  users.value = await getUsers()
}
onMounted(load)

async function createUserHandler() {
  if (!newName.value.trim() || !newEmail.value.trim()) return
  await createUser({ name: newName.value, email: newEmail.value, is_admin: newIsAdmin.value })
  newName.value = ''
  newEmail.value = ''
  newIsAdmin.value = false
  showCreate.value = false
  await load()
}

function startEdit(user: UserResponse) {
  editId.value = user.id
  editName.value = user.name
  editEmail.value = user.email
  editIsAdmin.value = user.is_admin
}

async function saveEdit(id: number) {
  if (!editName.value.trim() || !editEmail.value.trim()) return
  await updateUser(id, { name: editName.value, email: editEmail.value, is_admin: editIsAdmin.value })
  editId.value = null
  editName.value = ''
  editEmail.value = ''
  editIsAdmin.value = false
  await load()
}

function cancelEdit() {
  editId.value = null
  editName.value = ''
  editEmail.value = ''
  editIsAdmin.value = false
}

async function deleteUserHandler(id: number) {
  const user = users.value.find((u) => u.id === id)
  const userName = user ? user.name : 'this user'
  if (!confirm(`Are you sure you want to delete ${userName}? This action cannot be undone.`)) {
    return
  }
  await deleteUser(id)
  await load()
}

// Bulk upload functions
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  // Reset state
  csvData.value = []
  validationErrors.value = []
  skippedCount.value = 0
  uploadResults.value = { success: [], skipped: 0, errors: [] }

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
  const validData: UserCreate[] = []
  const csvEmails = new Set<string>()
  const existingEmails = new Set(users.value.map((u) => u.email.toLowerCase()))
  let skipped = 0

  if (data.length === 0) {
    errors.push('CSV file is empty')
    validationErrors.value = errors
    return
  }

  data.forEach((row, index) => {
    const rowNum = index + 2 // +2 because of header row and 0-based index

    // Validate name
    if (!row.name || !row.name.trim()) {
      errors.push(`Row ${rowNum}: 'name' is required`)
      return
    }

    if (row.name.trim().length < 2) {
      errors.push(`Row ${rowNum}: 'name' must be at least 2 characters`)
      return
    }

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

    // Skip rows whose email already exists in the system (not a blocking error)
    if (existingEmails.has(email)) {
      skipped++
      return
    }

    // Check for duplicate emails within the CSV
    if (csvEmails.has(email)) {
      errors.push(`Row ${rowNum}: duplicate email '${row.email.trim()}' found in CSV`)
      return
    }
    csvEmails.add(email)

    validData.push({
      name: row.name.trim(),
      email: row.email.trim(),
      is_admin: false,
    })
  })

  skippedCount.value = skipped

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
  uploadResults.value = { success: [], skipped: skippedCount.value, errors: [] }

  for (const element of csvData.value) {
    const user = element
    try {
      await createUser(user)
      uploadResults.value.success.push(`"${user.name}" (${user.email}) uploaded successfully`)
      uploadProgress.value.current++
    } catch (error: unknown) {
      let errorMessage = 'Unknown error'
      if (error && typeof error === 'object') {
        if (
          'response' in error &&
          error.response &&
          typeof error.response === 'object' &&
          'data' in error.response
        ) {
          const data = error.response.data
          if (data && typeof data === 'object' && 'detail' in data) {
            errorMessage = String(data.detail)
          }
        } else if ('message' in error) {
          errorMessage = String(error.message)
        }
      }
      uploadResults.value.errors.push(`"${user.name}" (${user.email}): ${errorMessage}`)
      uploadProgress.value.current++
    }
  }

  isUploading.value = false

  // Reload the users list
  await load()
}

function closeBulkUpload() {
  showBulkUpload.value = false
  csvData.value = []
  validationErrors.value = []
  skippedCount.value = 0
  uploadResults.value = { success: [], skipped: 0, errors: [] }
  uploadProgress.value = { current: 0, total: 0 }
  isUploading.value = false

  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}
</script>
