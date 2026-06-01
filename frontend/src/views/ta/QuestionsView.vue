<!--
  QuestionsView.vue (TA)
  TA can view list of questions.
-->
<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center mb-4">
      <h2 class="text-xl font-semibold">Questions</h2>
      <div class="flex gap-2 items-center w-full sm:w-auto shrink-0">
        <AppSelect v-model="filterSubjectId" class="w-full sm:w-48">
          <option value="">All Subjects</option>
          <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
            {{ subject.name }}
          </option>
        </AppSelect>
      </div>
    </div>
    <AppTable
      :isEmpty="filteredQuestions.length === 0"
      emptyMessage="No questions found. Adjust your filters to see available questions."
    >
      <template #head>
        <th>ID</th>
        <th>Subject</th>
        <th>Text</th>
      </template>
      <tr v-for="question in filteredQuestions" :key="question.id">
        <td>{{ question.id }}</td>
        <td>{{ getSubjectName(question.subject_id) }}</td>
        <td>{{ question.text }}</td>
      </tr>
    </AppTable>
  </div>
</template>

<script setup lang="ts">
// TA Questions list view
import { ref, onMounted, computed } from 'vue'
import AppTable from '../../components/common/AppTable.vue'
import AppSelect from '../../components/common/AppSelect.vue'
import { getQuestions, getSubjects } from '../../api/ta'
import type { QuestionResponse, SubjectResponse } from '../../types/api'

const questions = ref<QuestionResponse[]>([])
const subjects = ref<SubjectResponse[]>([])
const filterSubjectId = ref<number | string>('')

async function load() {
  ;[questions.value, subjects.value] = await Promise.all([getQuestions(), getSubjects()])
}
onMounted(load)

function getSubjectName(id: number) {
  return subjects.value.find((s) => s.id === id)?.name || ''
}

const filteredQuestions = computed(() => {
  if (filterSubjectId.value === '' || filterSubjectId.value === null) {
    return questions.value
  }
  return questions.value.filter((question) => question.subject_id === Number(filterSubjectId.value))
})
</script>
