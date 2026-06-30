// Admin API: CRUD for subjects, questions, users, lab sessions, session assignments, evaluations
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
  LabSession,
  LabSessionCreate,
  LabSessionUpdate,
  SessionAssignment,
  SessionAssignmentCreate,
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

// Lab Sessions
export const getLabSessions = async (subjectId?: number): Promise<LabSession[]> =>
  (await api.get('/admin/lab-sessions', { params: subjectId ? { subject_id: subjectId } : {} }))
    .data
export const getLabSession = async (id: number): Promise<LabSession> =>
  (await api.get(`/admin/lab-sessions/${id}`)).data
export const createLabSession = async (body: LabSessionCreate): Promise<LabSession> =>
  (await api.post('/admin/lab-sessions', body)).data
export const updateLabSession = async (id: number, body: LabSessionUpdate): Promise<LabSession> =>
  (await api.put(`/admin/lab-sessions/${id}`, body)).data
export const deleteLabSession = async (id: number) =>
  (await api.delete(`/admin/lab-sessions/${id}`)).data
export const setLabSessionAccepting = async (
  id: number,
  accepting: boolean,
): Promise<LabSession> =>
  (
    await api.patch(`/admin/lab-sessions/${id}/accepting`, null, {
      params: { accepting_evaluations: accepting },
    })
  ).data

// Session Assignments
export const getSessionAssignments = async (labSessionId?: number): Promise<SessionAssignment[]> =>
  (
    await api.get('/admin/session-assignments', {
      params: labSessionId ? { lab_session_id: labSessionId } : {},
    })
  ).data
export const getSessionAssignment = async (id: number): Promise<SessionAssignment> =>
  (await api.get(`/admin/session-assignments/${id}`)).data
export const createSessionAssignment = async (
  body: SessionAssignmentCreate,
): Promise<SessionAssignment> => (await api.post('/admin/session-assignments', body)).data
export const deleteSessionAssignment = async (id: number) =>
  (await api.delete(`/admin/session-assignments/${id}`)).data

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
