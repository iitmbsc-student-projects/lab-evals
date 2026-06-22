<!--
  EvaluationsView.vue (Admin)
  Admin can view, create, edit, and delete evaluations (override, unrestricted).
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Evaluations</h2>
        <p class="text-sm text-zinc-600 mt-1">Manage all evaluations (admin override)</p>
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
      emptyMessage="No evaluations found. Add your first evaluation or adjust your filters."
    >
      <template #head>
        <th>ID</th>
        <th>Student</th>
        <th>Subject</th>
        <th>Question</th>
        <th>TA</th>
        <th>Session</th>
        <th>Marking</th>
        <th>Remarks</th>
        <th>Actions</th>
      </template>
      <tr v-for="evaluation in filteredEvaluations" :key="evaluation.id">
        <td>{{ evaluation.id }}</td>
        <td>{{ getUserName(evaluation.student_id) }}</td>
        <td>{{ getQuestionSubject(evaluation.question_id) }}</td>
        <td>{{ getQuestionText(evaluation.question_id) }}</td>
        <td>{{ getUserName(evaluation.ta_id) }}</td>
        <td>{{ getSessionLabel(evaluation.lab_session_id) }}</td>
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
        <AppSelect v-model="newLabSessionId" label="Lab Session" required class="mb-3">
          <option :value="null">-- Select Lab Session --</option>
          <option v-for="session in labSessions" :key="session.id" :value="session.id">
            {{ getSessionLabel(session.id) }}
          </option>
        </AppSelect>
        <AppCombobox
          v-model="newStudentId"
          :options="studentOptions"
          @change="onStudentChange"
          label="Student"
          placeholder="Search student by name or email..."
          required
          class="mb-3"
        />
        <AppSelect
          v-model="newSubjectId"
          :disabled="!newStudentId"
          @change="onSubjectChange"
          label="Subject"
          required
          class="mb-3"
        >
          <option :value="null">-- Select Subject --</option>
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
          label="Question"
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
        <AppSelect v-model="newTaId" label="TA" required class="mb-3">
          <option v-for="user in nonAdminUsers" :key="user.id" :value="user.id">
            {{ user.name }} ({{ user.email }})
          </option>
        </AppSelect>
        <AppSelect v-model.number="newMarking" label="Marking" required class="mb-3">
          <option v-for="n in 5" :key="n" :value="n">{{ n }} / 5</option>
        </AppSelect>
        <AppInput v-model="newRemarks" placeholder="Remarks (optional)" label="Remarks" />
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showCreate = false" variant="ghost">Cancel</AppButton>
          <AppButton @click="createEvaluationHandler">Create Evaluation</AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Evaluations CRUD view
import { ref, onMounted, computed } from 'vue'
import AppButton from '../../components/common/AppButton.vue'
import AppInput from '../../components/common/AppInput.vue'
import AppSelect from '../../components/common/AppSelect.vue'
import AppCombobox from '../../components/common/AppCombobox.vue'
import AppTable from '../../components/common/AppTable.vue'
import {
  getEvaluations,
  createEvaluation,
  updateEvaluation,
  deleteEvaluation,
  getUsers,
  getQuestions,
  getSubjects,
  getLabSessions,
} from '../../api/admin'
import type {
  EvaluationResponse,
  UserResponse,
  QuestionResponse,
  Marking,
  SubjectResponse,
  LabSession,
} from '../../types/api'

const evaluations = ref<EvaluationResponse[]>([])
const users = ref<UserResponse[]>([])
const questions = ref<QuestionResponse[]>([])
const subjects = ref<SubjectResponse[]>([])
const labSessions = ref<LabSession[]>([])
const showCreate = ref(false)
const newLabSessionId = ref<number | null>(null)
const newStudentId = ref<number | null>(null)
const newSubjectId = ref<number | null>(null)
const newQuestionId = ref<number | null>(null)
const newTaId = ref<number | null>(null)
const newMarking = ref<Marking>(5)
const newRemarks = ref('')
const editId = ref<number | null>(null)
const editMarking = ref<Marking>(5)
const editRemarks = ref('')
const filterSubjectId = ref<number | string>('')

async function load() {
  ;[evaluations.value, users.value, questions.value, subjects.value, labSessions.value] =
    await Promise.all([
      getEvaluations(),
      getUsers(),
      getQuestions(),
      getSubjects(),
      getLabSessions(),
    ])
}
onMounted(load)

function getUserName(id: number) {
  return users.value.find((u) => u.id === id)?.name || ''
}
function getQuestionText(id: number) {
  return questions.value.find((q) => q.id === id)?.text || ''
}

function getQuestionSubject(questionId: number) {
  const question = questions.value.find((q) => q.id === questionId)
  if (!question) return ''
  return subjects.value.find((s) => s.id === question.subject_id)?.name || ''
}

function getSubjectName(id: number) {
  return subjects.value.find((s) => s.id === id)?.name || ''
}

function getSessionLabel(sessionId: number) {
  const session = labSessions.value.find((s) => s.id === sessionId)
  if (!session) return `Session #${sessionId}`
  return `${getSubjectName(session.subject_id)} — ${session.date}`
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

const nonAdminUsers = computed(() => {
  return users.value.filter((u) => !u.is_admin)
})

// Options for the searchable student combobox
const studentOptions = computed(() =>
  nonAdminUsers.value.map((u) => ({ value: u.id, label: `${u.name} (${u.email})` })),
)

const filteredSubjectsForStudent = computed(() => {
  if (!newStudentId.value) return []
  return subjects.value
})

const filteredQuestionsForSubject = computed(() => {
  if (!newSubjectId.value) return []
  return questions.value.filter((q) => q.subject_id === newSubjectId.value)
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
  if (
    !newLabSessionId.value ||
    !newStudentId.value ||
    !newQuestionId.value ||
    !newTaId.value ||
    !newMarking.value
  )
    return
  await createEvaluation({
    lab_session_id: newLabSessionId.value,
    student_id: newStudentId.value,
    question_id: newQuestionId.value,
    ta_id: newTaId.value,
    marking: newMarking.value,
    remarks: newRemarks.value || null,
  })
  newLabSessionId.value = null
  newStudentId.value = null
  newSubjectId.value = null
  newQuestionId.value = null
  newTaId.value = null
  newMarking.value = 5
  newRemarks.value = ''
  showCreate.value = false
  await load()
}

function startEdit(evaluation: EvaluationResponse) {
  editId.value = evaluation.id
  editMarking.value = evaluation.marking
  editRemarks.value = evaluation.remarks || ''
}

async function saveEdit(id: number) {
  const ev = evaluations.value.find((e) => e.id === id)
  if (!ev) return
  await updateEvaluation(id, {
    lab_session_id: ev.lab_session_id,
    student_id: ev.student_id,
    question_id: ev.question_id,
    ta_id: ev.ta_id,
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
