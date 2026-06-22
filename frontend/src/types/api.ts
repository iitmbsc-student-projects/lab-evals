// Types for API requests and responses, generated from OpenAPI spec
// Used throughout the app for type safety

export type SubjectRole = 'student' | 'ta'

export interface UserResponse {
  id: number
  name: string
  email: string
  is_admin: boolean
  created_at: string
}

export interface UserCreate {
  name: string
  email: string
  is_admin?: boolean
  google_sub?: string
}

export interface UserUpdate {
  name: string
  email: string
  is_admin?: boolean
}

export interface SubjectResponse {
  id: number
  name: string
  description?: string | null
}

export interface SubjectCreate {
  name: string
  description?: string | null
}

export interface SubjectUpdate {
  name: string
  description?: string | null
}

export interface QuestionResponse {
  id: number
  subject_id: number
  text: string
}

export interface QuestionCreate {
  subject_id: number
  text: string
}

export interface QuestionUpdate {
  subject_id: number
  text: string
}

export interface LabSession {
  id: number
  subject_id: number
  date: string
  accepting_evaluations: boolean
}

export interface LabSessionCreate {
  subject_id: number
  date: string
  accepting_evaluations?: boolean
}

export interface LabSessionUpdate {
  date: string
  accepting_evaluations: boolean
}

export interface SessionAssignment {
  id: number
  lab_session_id: number
  user_id: number
  role: SubjectRole
}

export interface SessionAssignmentCreate {
  lab_session_id: number
  user_id: number
  role: SubjectRole
}

export interface MySession {
  lab_session_id: number
  subject_id: number
  subject_name: string
  date: string
  role: SubjectRole
  accepting_evaluations: boolean
}

// Evaluation rating: integer 1-5 (5 = best).
export type Marking = 1 | 2 | 3 | 4 | 5

export interface EvaluationResponse {
  id: number
  lab_session_id: number
  student_id: number
  question_id: number
  ta_id: number
  marking: Marking
  remarks?: string | null
}

export interface EvaluationUpdate {
  student_id: number
  question_id: number
  ta_id: number
  marking: Marking
  remarks?: string | null
}

export interface TAEvaluationCreate {
  lab_session_id: number
  student_id: number
  question_id: number
  marking: Marking
  remarks?: string | null
}

export interface TAEvaluationResponse {
  id: number
  lab_session_id: number
  student_id: number
  question_id: number
  marking: Marking
  ta_id: number
  remarks?: string | null
}

export interface TAEvaluationUpdate {
  marking: Marking
  remarks?: string | null
}

export interface StudentEvaluationResponse {
  id: number
  lab_session_id: number
  student_id: number
  question_id: number
  ta_id: number
}

export interface TokenRequest {
  id_token: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
