// Types for API requests and responses, generated from OpenAPI spec
// Used throughout the app for type safety

export type UserRole = 'admin' | 'ta' | 'student'

export interface UserResponse {
  id: number
  name: string
  email: string
  role: UserRole
  created_at: string
}

export interface UserCreate {
  name: string
  email: string
  role: UserRole
}

export interface UserUpdate {
  name: string
  email: string
  role: UserRole
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

export interface EnrollmentResponse {
  id: number
  user_id: number
  subject_id: number
}

export interface EnrollmentCreate {
  user_id: number
  subject_id: number
}

// Evaluation rating: integer 1-5 (5 = best).
export type Marking = 1 | 2 | 3 | 4 | 5

export interface EvaluationResponse {
  id: number
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
  student_id: number
  question_id: number
  marking: Marking
  remarks?: string | null
}

export interface TAEvaluationResponse {
  id: number
  student_id: number
  question_id: number
  marking: Marking
  ta_id: number
  remarks?: string | null
}

export interface TAEvaluationUpdate {
  student_id: number
  question_id: number
  marking: Marking
  remarks?: string | null
}

export interface TokenRequest {
  id_token: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
