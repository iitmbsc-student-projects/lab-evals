<!--
  SubjectsView.vue (Admin)
  Admin can view, create, edit, and delete subjects.
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Subjects</h2>
        <p class="text-sm text-zinc-600 mt-1">Manage subjects and bulk upload via CSV</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButton @click="showCreate = true">Add Subject</AppButton>
        <AppButton @click="showBulkUpload = true" variant="secondary">Bulk Upload CSV</AppButton>
      </div>
    </div>

    <AppTable
      :isEmpty="subjects.length === 0"
      emptyMessage="No subjects created yet. Add your first subject to get started."
    >
      <template #head>
        <th>ID</th>
        <th>Name</th>
        <th>Description</th>
        <th>Actions</th>
      </template>
      <tr v-for="subject in subjects" :key="subject.id">
        <td class="font-mono text-xs text-zinc-500">{{ subject.id }}</td>
        <td v-if="editId !== subject.id" class="font-medium">{{ subject.name }}</td>
        <td v-else>
          <AppInput v-model="editName" />
        </td>
        <td v-if="editId !== subject.id" class="text-zinc-600">{{ subject.description || '-' }}</td>
        <td v-else>
          <AppInput v-model="editDescription" />
        </td>
        <td>
          <div class="flex gap-2">
            <AppButton
              v-if="editId !== subject.id"
              @click="startEdit(subject)"
              variant="secondary"
              size="sm"
              >Edit</AppButton
            >
            <AppButton
              v-if="editId === subject.id"
              @click="saveEdit(subject.id)"
              variant="success"
              size="sm"
              >Save</AppButton
            >
            <AppButton v-if="editId === subject.id" @click="cancelEdit" variant="ghost" size="sm"
              >Cancel</AppButton
            >
            <AppButton variant="danger" size="sm" @click="deleteSubjectHandler(subject.id)"
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
          <h3 class="text-lg font-semibold text-zinc-900">Add Subject</h3>
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
        <AppInput
          v-model="newName"
          placeholder="Subject name"
          label="Subject Name"
          required
          class="mb-3"
        />
        <AppInput
          v-model="newDescription"
          placeholder="Description (optional)"
          label="Description"
        />
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showCreate = false" variant="ghost">Cancel</AppButton>
          <AppButton @click="createSubjectHandler">Create Subject</AppButton>
        </div>
      </div>
    </div>

    <!-- Bulk Upload Modal -->
    <div
      v-if="showBulkUpload"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white p-6 rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-auto">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-zinc-900">Bulk Upload Subjects</h3>
          <button
            @click="closeBulkUpload"
            :disabled="isUploading"
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

        <div class="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm">
          <p class="font-semibold mb-2 text-blue-900">CSV Format:</p>
          <p class="text-blue-800 mb-2">Your CSV file should have the following columns:</p>
          <ul class="list-disc list-inside mt-1 text-blue-800 space-y-1">
            <li><strong>name</strong> (required): Subject name</li>
            <li><strong>description</strong> (optional): Subject description</li>
          </ul>
          <p class="mt-3 mb-1 font-medium text-blue-900">Example:</p>
          <code class="block mt-1 p-3 bg-white rounded border border-blue-200 text-xs">
            name,description<br />
            Mathematics,Introduction to Algebra<br />
            Physics,Classical Mechanics
          </code>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept=".csv"
          @change="handleFileSelect"
          class="mb-4 block w-full text-sm text-zinc-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-zinc-800 file:text-white hover:file:bg-zinc-700 cursor-pointer"
        />

        <!-- Validation Errors -->
        <div
          v-if="validationErrors.length > 0"
          class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg"
        >
          <p class="font-semibold text-red-800 mb-2">Validation Errors:</p>
          <ul class="text-sm text-red-700 list-disc list-inside max-h-40 overflow-auto space-y-1">
            <li v-for="(error, idx) in validationErrors" :key="idx">{{ error }}</li>
          </ul>
        </div>

        <!-- Preview Table -->
        <div v-if="csvData.length > 0 && validationErrors.length === 0" class="mb-4">
          <p class="font-semibold mb-2">Preview ({{ csvData.length }} subjects):</p>
          <div class="border rounded-lg overflow-hidden">
            <div class="max-h-60 overflow-auto">
              <table class="w-full text-sm">
                <thead class="bg-zinc-50 sticky top-0">
                  <tr>
                    <th class="px-4 py-2 text-left font-semibold text-zinc-700">Name</th>
                    <th class="px-4 py-2 text-left font-semibold text-zinc-700">Description</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-200">
                  <tr v-for="(row, idx) in csvData" :key="idx" class="hover:bg-zinc-50">
                    <td class="px-4 py-2">{{ row.name }}</td>
                    <td class="px-4 py-2 text-zinc-600">{{ row.description || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Progress Bar -->
        <div v-if="isUploading" class="mb-4">
          <div class="flex justify-between text-sm mb-2">
            <span class="font-medium text-zinc-700">Uploading...</span>
            <span class="text-zinc-600"
              >{{ uploadProgress.current }} / {{ uploadProgress.total }}</span
            >
          </div>
          <div class="w-full bg-zinc-200 rounded-full h-3 overflow-hidden">
            <div
              class="bg-green-600 h-full transition-all duration-300 rounded-full"
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
            class="mb-3 p-4 bg-green-50 border border-green-200 rounded-lg"
          >
            <p class="text-green-800 font-semibold flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Successfully uploaded {{ uploadResults.success.length }} subjects
            </p>
          </div>
          <div
            v-if="uploadResults.errors.length > 0"
            class="p-4 bg-red-50 border border-red-200 rounded-lg"
          >
            <p class="font-semibold text-red-800 mb-2">Failed uploads:</p>
            <ul class="text-sm text-red-700 list-disc list-inside max-h-40 overflow-auto space-y-1">
              <li v-for="(error, idx) in uploadResults.errors" :key="idx">{{ error }}</li>
            </ul>
          </div>
        </div>

        <div class="flex gap-2 justify-end">
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
            variant="success"
          >
            Upload {{ csvData.length }} Subjects
          </AppButton>
          <AppButton @click="closeBulkUpload" :disabled="isUploading" variant="ghost">
            {{ isUploading ? 'Uploading...' : 'Close' }}
          </AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Subjects CRUD view
import { ref, onMounted } from 'vue'
import Papa from 'papaparse'
import AppButton from '../../components/common/AppButton.vue'
import AppInput from '../../components/common/AppInput.vue'
import AppTable from '../../components/common/AppTable.vue'
import { getSubjects, createSubject, updateSubject, deleteSubject } from '../../api/admin'
import type { SubjectResponse, SubjectCreate } from '../../types/api'

const subjects = ref<SubjectResponse[]>([])
const showCreate = ref(false)
const newName = ref('')
const newDescription = ref('')
const editId = ref<number | null>(null)
const editName = ref('')
const editDescription = ref('')

// Bulk upload state
const showBulkUpload = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const csvData = ref<SubjectCreate[]>([])
const validationErrors = ref<string[]>([])
const isUploading = ref(false)
const uploadProgress = ref({ current: 0, total: 0 })
const uploadResults = ref<{ success: string[]; errors: string[] }>({ success: [], errors: [] })

async function load() {
  subjects.value = await getSubjects()
}
onMounted(load)

async function createSubjectHandler() {
  if (!newName.value.trim()) return
  await createSubject({
    name: newName.value,
    description: newDescription.value.trim() || null,
  })
  newName.value = ''
  newDescription.value = ''
  showCreate.value = false
  await load()
}

function startEdit(subject: SubjectResponse) {
  editId.value = subject.id
  editName.value = subject.name
  editDescription.value = subject.description || ''
}

async function saveEdit(id: number) {
  if (!editName.value.trim()) return
  await updateSubject(id, {
    name: editName.value,
    description: editDescription.value.trim() || null,
  })
  editId.value = null
  editName.value = ''
  editDescription.value = ''
  await load()
}

function cancelEdit() {
  editId.value = null
  editName.value = ''
  editDescription.value = ''
}

async function deleteSubjectHandler(id: number) {
  const subject = subjects.value.find((s) => s.id === id)
  const subjectName = subject ? subject.name : 'this subject'
  if (!confirm(`Are you sure you want to delete ${subjectName}? This action cannot be undone.`)) {
    return
  }
  await deleteSubject(id)
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
  const validData: SubjectCreate[] = []

  if (data.length === 0) {
    errors.push('CSV file is empty')
    validationErrors.value = errors
    return
  }

  data.forEach((row, index) => {
    const rowNum = index + 2 // +2 because of header row and 0-based index

    // Validate required fields
    if (!row.name || !row.name.trim()) {
      errors.push(`Row ${rowNum}: 'name' is required`)
      return
    }

    // Check if name is too short
    if (row.name.trim().length < 2) {
      errors.push(`Row ${rowNum}: 'name' must be at least 2 characters`)
      return
    }

    validData.push({
      name: row.name.trim(),
      description: row.description?.trim() || null,
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
    const subject = element
    try {
      await createSubject(subject)
      uploadResults.value.success.push(`"${subject.name}" uploaded successfully`)
      uploadProgress.value.current++
    } catch (error) {
      let errorMessage = 'Unknown error'
      if (error instanceof Error) {
        errorMessage = error.message
      } else if (error && typeof error === 'object' && 'response' in error) {
        const response = (error as { response?: { data?: { detail?: string; message?: string } } })
          .response
        errorMessage = response?.data?.detail || response?.data?.message || 'Unknown error'
      }
      uploadResults.value.errors.push(`"${subject.name}": ${errorMessage}`)
      uploadProgress.value.current++
    }
  }

  isUploading.value = false

  // Reload the subjects list
  await load()
}

function closeBulkUpload() {
  showBulkUpload.value = false
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
