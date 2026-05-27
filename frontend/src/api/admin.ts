// Admin API: CRUD for subjects, questions, users, enrollments, evaluations
import api from './client'
import type {
  SubjectResponse,
  SubjectCreate,
  SubjectUpdate,
  QuestionResponse,
  QuestionCreate,
  QuestionUpdate,
  UserResponse,
  UserCreate,
  UserUpdate,
  EnrollmentResponse,
  EnrollmentCreate,
  EvaluationResponse,
  EvaluationUpdate,
} from '../types/api'

// Subjects
export const getSubjects = async (): Promise<SubjectResponse[]> =>
  (await api.get('/admin/subjects')).data
export const createSubject = async (body: SubjectCreate) =>
  (await api.post('/admin/subjects', body)).data
export const updateSubject = async (id: number, body: SubjectUpdate) =>
  (await api.put(`/admin/subjects/${id}`, body)).data
export const deleteSubject = async (id: number) => (await api.delete(`/admin/subjects/${id}`)).data

// Questions
export const getQuestions = async (): Promise<QuestionResponse[]> =>
  (await api.get('/admin/questions')).data
export const createQuestion = async (body: QuestionCreate) =>
  (await api.post('/admin/questions', body)).data
export const updateQuestion = async (id: number, body: QuestionUpdate) =>
  (await api.put(`/admin/questions/${id}`, body)).data
export const deleteQuestion = async (id: number) =>
  (await api.delete(`/admin/questions/${id}`)).data

// Users
export const getUsers = async (): Promise<UserResponse[]> => (await api.get('/admin/users')).data
export const createUser = async (body: UserCreate) => (await api.post('/admin/users', body)).data
export const updateUser = async (id: number, body: UserUpdate) =>
  (await api.put(`/admin/users/${id}`, body)).data
export const deleteUser = async (id: number) => (await api.delete(`/admin/users/${id}`)).data

// Enrollments
export const getEnrollments = async (): Promise<EnrollmentResponse[]> =>
  (await api.get('/admin/enrollments')).data
export const createEnrollment = async (body: EnrollmentCreate) =>
  (await api.post('/admin/enrollments', body)).data
export const deleteEnrollment = async (id: number) =>
  (await api.delete(`/admin/enrollments/${id}`)).data

// Evaluations
export const getEvaluations = async (): Promise<EvaluationResponse[]> =>
  (await api.get('/admin/evaluations')).data
export const createEvaluation = async (body: EvaluationUpdate) =>
  (await api.post('/admin/evaluations/', body)).data
export const updateEvaluation = async (id: number, body: EvaluationUpdate) =>
  (await api.put(`/admin/evaluations/${id}`, body)).data
export const deleteEvaluation = async (id: number) =>
  (await api.delete(`/admin/evaluations/${id}`)).data

// Audit
export interface AuditExportParams {
  from_date?: string
  to_date?: string
  actor_user_id?: number
  action?: string
  resource_type?: string
}

export async function exportAuditCsv(params: AuditExportParams): Promise<void> {
  const response = await api.get('/admin/audit/export.csv', {
    params,
    responseType: 'blob',
  })

  const disposition = response.headers['content-disposition'] as string | undefined
  const filename = disposition?.match(/filename="([^"]+)"/)?.[1] ?? 'audit.csv'

  const url = URL.createObjectURL(response.data as Blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
