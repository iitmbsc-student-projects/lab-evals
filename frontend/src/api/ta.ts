// TA API: Session-scoped calls for students, questions, evaluations
import api from './client'
import type {
  UserResponse,
  QuestionResponse,
  TAEvaluationCreate,
  TAEvaluationResponse,
  TAEvaluationUpdate,
} from '../types/api'

// Get own user info
export const getMe = async (): Promise<UserResponse> => (await api.get('/user/me')).data

// List students assigned to a session
export const getStudents = async (sessionId: number): Promise<UserResponse[]> =>
  (await api.get(`/ta/sessions/${sessionId}/students`)).data

// List questions for a session
export const getQuestions = async (sessionId: number): Promise<QuestionResponse[]> =>
  (await api.get(`/ta/sessions/${sessionId}/questions`)).data

// List evaluations for a session
export const getEvaluations = async (sessionId: number): Promise<TAEvaluationResponse[]> =>
  (await api.get(`/ta/sessions/${sessionId}/evaluations`)).data

// Create evaluation for a session
export const createEvaluation = async (
  sessionId: number,
  body: TAEvaluationCreate,
): Promise<TAEvaluationResponse> =>
  (await api.post(`/ta/sessions/${sessionId}/evaluations`, body)).data

// Update evaluation in a session
export const updateEvaluation = async (
  sessionId: number,
  evaluationId: number,
  body: TAEvaluationUpdate,
): Promise<TAEvaluationResponse> =>
  (await api.put(`/ta/sessions/${sessionId}/evaluations/${evaluationId}`, body)).data

// Delete evaluation from a session
export const deleteEvaluation = async (sessionId: number, evaluationId: number) =>
  (await api.delete(`/ta/sessions/${sessionId}/evaluations/${evaluationId}`)).data
