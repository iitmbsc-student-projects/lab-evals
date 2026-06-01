<!--
  EvaluationsView.vue (TA)
  TA can view, create, edit, and delete their own evaluations.
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Evaluations</h2>
        <p class="text-sm text-zinc-600 mt-1">Manage your student evaluations</p>
      </div>
      <AppButton class="self-start sm:self-auto shrink-0" @click="showCreate = true"
        >Add Evaluation</AppButton
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
      :isEmpty="filteredEvaluations.length === 0"
      emptyMessage="No evaluations assigned to you yet. Check back later or adjust your filters."
    >
      <template #head>
        <th>ID</th>
        <th>Student Name</th>
        <th>Student Email</th>
        <th>Subject</th>
        <th>Question</th>
        <th>Marking</th>
        <th>Remarks</th>
        <th>Actions</th>
      </template>
      <tr v-for="evaluation in filteredEvaluations" :key="evaluation.id">
        <td>{{ evaluation.id }}</td>
        <td>{{ getUserName(evaluation.student_id) }}</td>
        <td>{{ getUserEmail(evaluation.student_id) }}</td>
        <td>{{ getQuestionSubject(evaluation.question_id) }}</td>
        <td>{{ getQuestionText(evaluation.question_id) }}</td>
        <td v-if="editId !== evaluation.id">{{ evaluation.marking }} / 5</td>
        <td v-else>
          <AppSelect v-model.number="editMarking">
            <option v-for="n in 5" :key="n" :value="n">{{ n }} / 5</option>
          </AppSelect>
        </td>
        <td v-if="editId !== evaluation.id">{{ evaluation.remarks }}</td>
        <td v-else>
          <AppInput v-model="editRemarks" />
        </td>
        <td>
          <div class="flex gap-2">
            <AppButton
              v-if="editId !== evaluation.id"
              @click="startEdit(evaluation)"
              variant="secondary"
              size="sm"
              >Edit</AppButton
            >
            <AppButton
              v-if="editId === evaluation.id"
              @click="saveEdit(evaluation.id)"
              variant="success"
              size="sm"
              >Save</AppButton
            >
            <AppButton v-if="editId === evaluation.id" @click="cancelEdit" variant="ghost" size="sm"
              >Cancel</AppButton
            >
            <AppButton variant="danger" size="sm" @click="deleteEvaluationHandler(evaluation.id)"
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
        class="bg-white p-6 rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto animate-in fade-in zoom-in duration-200"
      >
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-zinc-900">Add Evaluation</h3>
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
        <AppCombobox
          v-model="newStudentId"
          :options="studentOptions"
          @change="onStudentChange"
          label="Select Student"
          placeholder="Search student by name or email..."
          required
          class="mb-3"
        />
        <AppSelect
          v-model="newSubjectId"
          :disabled="!newStudentId"
          @change="onSubjectChange"
          label="Select Subject"
          required
          class="mb-3"
        >
          <option
            v-for="subject in filteredSubjectsForStudent"
            :key="subject.id"
            :value="subject.id"
          >
            {{ subject.name }}
          </option>
        </AppSelect>
        <AppSelect
          v-model="newQuestionId"
          :disabled="!newSubjectId"
          label="Select Question"
          required
          class="mb-3"
        >
          <option
            v-for="question in filteredQuestionsForSubject"
            :key="question.id"
            :value="question.id"
          >
            {{ question.text }}
          </option>
        </AppSelect>
        <AppSelect v-model.number="newMarking" label="Select Marking" required class="mb-3">
          <option v-for="n in 5" :key="n" :value="n">{{ n }} / 5</option>
        </AppSelect>
        <AppInput
          v-model="newRemarks"
          placeholder="Remarks (optional)"
          label="Remarks (Optional)"
        />
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showCreate = false" variant="ghost">Cancel</AppButton>
          <AppButton @click="createEvaluationHandler">Create Evaluation</AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// TA Evaluations CRUD (self only)
import { ref, onMounted, computed } from 'vue'
import AppButton from '@/components/common/AppButton.vue'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppCombobox from '@/components/common/AppCombobox.vue'
import AppTable from '@/components/common/AppTable.vue'
import {
  getEvaluations,
  createEvaluation,
  updateEvaluation,
  deleteEvaluation,
  getStudents,
  getQuestions,
  getSubjects,
  getEnrollments,
} from '@/api/ta'
import {
  type TAEvaluationResponse,
  type UserResponse,
  type QuestionResponse,
  type Marking,
  type SubjectResponse,
  type EnrollmentResponse,
} from '@/types/api'

const evaluations = ref<TAEvaluationResponse[]>([])
const users = ref<UserResponse[]>([])
const questions = ref<QuestionResponse[]>([])
const subjects = ref<SubjectResponse[]>([])
const showCreate = ref(false)
const newStudentId = ref<number | null>(null)
const newSubjectId = ref<number | null>(null)
const newQuestionId = ref<number | null>(null)
const newMarking = ref<Marking>(5)
const newRemarks = ref('')
const editId = ref<number | null>(null)
const editMarking = ref<Marking>(5)
const editRemarks = ref('')
const enrollments = ref<EnrollmentResponse[]>([])
const filterSubjectId = ref<number | string>('')

async function load() {
  ;[evaluations.value, users.value, questions.value, subjects.value, enrollments.value] =
    await Promise.all([
      getEvaluations(),
      getStudents(),
      getQuestions(),
      getSubjects(),
      getEnrollments(),
    ])
}
onMounted(load)

function getUserName(id: number) {
  return users.value.find((u) => u.id === id)?.name || ''
}

function getUserEmail(id: number) {
  return users.value.find((u) => u.id === id)?.email || ''
}

function getQuestionText(id: number) {
  return questions.value.find((q) => q.id === id)?.text || ''
}

function getQuestionSubject(questionId: number) {
  const question = questions.value.find((q) => q.id === questionId)
  if (!question) return ''
  return subjects.value.find((s) => s.id === question.subject_id)?.name || ''
}

const filteredEvaluations = computed(() => {
  if (filterSubjectId.value === '' || filterSubjectId.value === null) {
    return evaluations.value
  }
  return evaluations.value.filter((evaluation) => {
    const question = questions.value.find((q) => q.id === evaluation.question_id)
    return question?.subject_id === Number(filterSubjectId.value)
  })
})

// Options for the searchable student combobox
const studentOptions = computed(() =>
  users.value.map((u) => ({ value: u.id, label: `${u.name} (${u.email})` })),
)

// Get subjects that both the student and TA are enrolled in
const filteredSubjectsForStudent = computed(() => {
  if (!newStudentId.value) return []

  // Get student's enrolled subject IDs
  const studentSubjectIds = enrollments.value
    .filter((e) => e.user_id === newStudentId.value)
    .map((e) => e.subject_id)

  if (studentSubjectIds.length === 0) return []

  // Return subjects that the student is enrolled in
  return subjects.value.filter((s) => studentSubjectIds.includes(s.id))
})

// Get questions for the selected subject that don't have evaluations yet for this student
const filteredQuestionsForSubject = computed(() => {
  if (!newStudentId.value || !newSubjectId.value) return []

  // Get questions for the selected subject
  const subjectQuestions = questions.value.filter((q) => q.subject_id === newSubjectId.value)

  // Filter out questions that already have evaluations for this student
  return subjectQuestions.filter(
    (q) =>
      !evaluations.value.some(
        (ev) => ev.student_id === newStudentId.value && ev.question_id === q.id,
      ),
  )
})

function onStudentChange() {
  // Reset subject and question when student changes
  newSubjectId.value = null
  newQuestionId.value = null
}

function onSubjectChange() {
  // Reset question when subject changes
  newQuestionId.value = null
}

async function createEvaluationHandler() {
  if (!newStudentId.value || !newQuestionId.value || !newMarking.value) return
  await createEvaluation({
    student_id: newStudentId.value,
    question_id: newQuestionId.value,
    marking: newMarking.value,
    remarks: newRemarks.value || null,
  })
  newStudentId.value = null
  newQuestionId.value = null
  newMarking.value = 5
  newRemarks.value = ''
  showCreate.value = false
  await load()
}

function startEdit(evaluation: TAEvaluationResponse) {
  editId.value = evaluation.id
  editMarking.value = evaluation.marking
  editRemarks.value = evaluation.remarks || ''
}

async function saveEdit(id: number) {
  const ev = evaluations.value.find((e) => e.id === id)
  if (!ev) return
  await updateEvaluation(id, {
    student_id: ev.student_id,
    question_id: ev.question_id,
    marking: editMarking.value,
    remarks: editRemarks.value || null,
  })
  editId.value = null
  editMarking.value = 5
  editRemarks.value = ''
  await load()
}

function cancelEdit() {
  editId.value = null
  editMarking.value = 5
  editRemarks.value = ''
}

async function deleteEvaluationHandler(id: number) {
  if (!confirm('Are you sure you want to delete this evaluation? This action cannot be undone.')) {
    return
  }
  await deleteEvaluation(id)
  await load()
}
</script>
