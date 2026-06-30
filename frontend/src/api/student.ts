// Student API: Session-scoped calls for questions and evaluations
import api from './client'
import type { QuestionResponse, StudentEvaluationResponse } from '../types/api'

// Get questions for a session
export const getQuestions = async (sessionId: number): Promise<QuestionResponse[]> =>
  (await api.get(`/student/sessions/${sessionId}/questions`)).data

// Get own evaluations for a session (presence-only, no marks)
export const getEvaluations = async (sessionId: number): Promise<StudentEvaluationResponse[]> =>
  (await api.get(`/student/sessions/${sessionId}/evaluations`)).data
