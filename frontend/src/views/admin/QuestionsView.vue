<!--
  QuestionsView.vue (Admin)
  Admin can view, create, edit, and delete questions.
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Questions</h2>
        <p class="text-sm text-zinc-600 mt-1">Manage questions and bulk upload via CSV</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButton @click="showCreate = true">Add Question</AppButton>
        <AppButton @click="showBulkUpload = true" variant="secondary">Bulk Upload CSV</AppButton>
      </div>
    </div>
    <!-- Subject Filter -->
    <div class="mb-4">
      <AppSelect v-model="selectedSubjectId" label="Filter by Subject" class="max-w-xs">
        <option value="">All Subjects</option>
        <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
          {{ subject.name }}
        </option>
      </AppSelect>
    </div>
    <AppTable
      :isEmpty="filteredQuestions.length === 0"
      emptyMessage="No questions found. Add your first question or adjust your filters."
    >
      <template #head>
        <th>ID</th>
        <th>Subject</th>
        <th>Text</th>
        <th>Actions</th>
      </template>
      <tr v-for="question in filteredQuestions" :key="question.id">
        <td>{{ question.id }}</td>
        <td>{{ getSubjectName(question.subject_id) }}</td>
        <td v-if="editId !== question.id">{{ question.text }}</td>
        <td v-else>
          <AppInput v-model="editText" />
        </td>
        <td>
          <div class="flex gap-2">
            <AppButton
              v-if="editId !== question.id"
              @click="startEdit(question)"
              variant="secondary"
              size="sm"
              >Edit</AppButton
            >
            <AppButton
              v-if="editId === question.id"
              @click="saveEdit(question.id)"
              variant="success"
              size="sm"
              >Save</AppButton
            >
            <AppButton v-if="editId === question.id" @click="cancelEdit" variant="ghost" size="sm"
              >Cancel</AppButton
            >
            <AppButton variant="danger" size="sm" @click="deleteQuestionHandler(question.id)"
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
          <h3 class="text-lg font-semibold text-zinc-900">Add Question</h3>
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
          <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
            {{ subject.name }}
          </option>
        </AppSelect>
        <AppInput v-model="newText" placeholder="Question text" label="Question Text" required />
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showCreate = false" variant="ghost">Cancel</AppButton>
          <AppButton @click="createQuestionHandler">Create Question</AppButton>
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
          <h3 class="text-lg font-semibold text-zinc-900">Bulk Upload Questions</h3>
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
            <li><strong>subject_id</strong> (required): Numeric ID of the subject</li>
            <li><strong>text</strong> (required): Question text</li>
          </ul>
          <p class="mt-2">Available Subjects:</p>
          <ul class="list-disc list-inside ml-4 text-xs mt-1 max-h-24 overflow-auto">
            <li v-for="subject in subjects" :key="subject.id">
              ID: {{ subject.id }} - {{ subject.name }}
            </li>
          </ul>
          <p class="mt-2">Example:</p>
          <code class="block mt-1 p-2 bg-white rounded">
            subject_id,text<br />
            1,What is the capital of France?<br />
            2,Explain Newton's first law of motion
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
          <p class="font-semibold mb-2">Preview ({{ csvData.length }} questions):</p>
          <div class="border rounded max-h-60 overflow-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50 sticky top-0">
                <tr>
                  <th class="px-3 py-2 text-left">Subject</th>
                  <th class="px-3 py-2 text-left">Question Text</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in csvData" :key="idx" class="border-t">
                  <td class="px-3 py-2">{{ getSubjectName(row.subject_id) }}</td>
                  <td class="px-3 py-2">{{ row.text }}</td>
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
              ✓ Successfully uploaded {{ uploadResults.success.length }} questions
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
            Upload {{ csvData.length }} Questions
          </AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Questions CRUD view
import { ref, onMounted, computed } from 'vue'
import Papa from 'papaparse'
import AppButton from '../../components/common/AppButton.vue'
import AppInput from '../../components/common/AppInput.vue'
import AppSelect from '../../components/common/AppSelect.vue'
import AppTable from '../../components/common/AppTable.vue'
import {
  getQuestions,
  createQuestion,
  updateQuestion,
  deleteQuestion,
  getSubjects,
} from '../../api/admin'
import type { QuestionResponse, SubjectResponse, QuestionCreate } from '../../types/api'

const questions = ref<QuestionResponse[]>([])
const subjects = ref<SubjectResponse[]>([])
const selectedSubjectId = ref<number | null>(null)
const showCreate = ref(false)
const newSubjectId = ref<number | null>(null)
const newText = ref('')
const editId = ref<number | null>(null)
const editText = ref('')
const editSubjectId = ref<number | null>(null)

// Bulk upload state
const showBulkUpload = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const csvData = ref<QuestionCreate[]>([])
const validationErrors = ref<string[]>([])
const isUploading = ref(false)
const uploadProgress = ref({ current: 0, total: 0 })
const uploadResults = ref<{ success: string[]; errors: string[] }>({ success: [], errors: [] })

async function load() {
  ;[questions.value, subjects.value] = await Promise.all([getQuestions(), getSubjects()])
}
onMounted(load)
const filteredQuestions = computed(() => {
  if (selectedSubjectId.value === null) {
    return questions.value
  }
  return questions.value.filter((q) => q.subject_id === selectedSubjectId.value)
})

function getSubjectName(id: number) {
  return subjects.value.find((s) => s.id === id)?.name || ''
}

async function createQuestionHandler() {
  if (!newSubjectId.value || !newText.value.trim()) return
  await createQuestion({ subject_id: newSubjectId.value, text: newText.value })
  newSubjectId.value = null
  newText.value = ''
  showCreate.value = false
  await load()
}

function startEdit(question: QuestionResponse) {
  editId.value = question.id
  editText.value = question.text
  editSubjectId.value = question.subject_id
}

async function saveEdit(id: number) {
  if (!editText.value.trim() || !editSubjectId.value) return
  await updateQuestion(id, { subject_id: editSubjectId.value, text: editText.value })
  editId.value = null
  editText.value = ''
  editSubjectId.value = null
  await load()
}

function cancelEdit() {
  editId.value = null
  editText.value = ''
  editSubjectId.value = null
}

async function deleteQuestionHandler(id: number) {
  if (!confirm('Are you sure you want to delete this question? This action cannot be undone.')) {
    return
  }
  await deleteQuestion(id)
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
  const validData: QuestionCreate[] = []

  if (data.length === 0) {
    errors.push('CSV file is empty')
    validationErrors.value = errors
    return
  }

  data.forEach((row, index) => {
    const rowNum = index + 2 // +2 because of header row and 0-based index

    // Validate subject_id
    if (!row.subject_id || !row.subject_id.trim()) {
      errors.push(`Row ${rowNum}: 'subject_id' is required`)
      return
    }

    const subjectId = parseInt(row.subject_id.trim())
    if (isNaN(subjectId)) {
      errors.push(`Row ${rowNum}: 'subject_id' must be a valid number`)
      return
    }

    // Check if subject exists
    const subjectExists = subjects.value.some((s) => s.id === subjectId)
    if (!subjectExists) {
      errors.push(`Row ${rowNum}: subject_id ${subjectId} does not exist`)
      return
    }

    // Validate text
    if (!row.text || !row.text.trim()) {
      errors.push(`Row ${rowNum}: 'text' is required`)
      return
    }

    // Check if text is too short
    if (row.text.trim().length < 3) {
      errors.push(`Row ${rowNum}: 'text' must be at least 3 characters`)
      return
    }

    validData.push({
      subject_id: subjectId,
      text: row.text.trim(),
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
    const question = element
    try {
      await createQuestion(question)
      uploadResults.value.success.push(`"${question.text}" uploaded successfully`)
      uploadProgress.value.current++
    } catch (error) {
      let errorMessage = 'Unknown error'
      if (error instanceof Error) {
        errorMessage = error.message
      } else if (error && typeof error === 'object' && 'response' in error) {
        const response = (error as { response: { data: { detail?: string } } }).response
        errorMessage = response.data?.detail || 'Unknown error'
      }
      uploadResults.value.errors.push(`"${question.text}": ${errorMessage}`)
      uploadProgress.value.current++
    }
  }

  isUploading.value = false

  // Reload the questions list
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
