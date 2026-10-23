/**
 * Types and interfaces for Teacher Quiz Builder, Settings, and Publishing (DEC-006, DEC-008, DEC-014).
 */
import type { Question } from './question'

export type QuizStatus = 'draft' | 'published' | 'closed' | 'archived'
export type MultiAnswerPolicy = 'all_or_nothing' | 'partial_with_penalty' | 'partial_no_penalty'

export interface DifficultyBreakdown {
  easy: number
  medium: number
  hard: number
}

export interface QuizCreatePayload {
  title: string
  course_code: string
  description?: string
  opens_at: string
  closes_at: string
  duration_minutes: number
  max_attempts: number
  allow_backtracking: boolean
  shuffle_questions: boolean
  shuffle_options: boolean
  multi_answer_policy: MultiAnswerPolicy
  tab_switch_limit: number
  tab_switch_penalty_marks: number
}

export interface QuizUpdatePayload extends QuizCreatePayload {}

export interface QuizListItem {
  id: string
  title: string
  course_code: string
  description?: string | null
  status: QuizStatus
  created_by_id: string
  current_version_id?: string | null
  version_number: number
  is_published: boolean
  opens_at: string
  closes_at: string
  duration_minutes: number
  total_questions: number
  total_marks: number
  difficulty_breakdown: DifficultyBreakdown
  created_at: string
  updated_at: string
}

export interface QuizListResponse {
  items: QuizListItem[]
  total: number
}

export interface QuizVersion {
  id: string
  quiz_id: string
  version_number: number
  title: string
  description?: string | null
  is_published: boolean
  opens_at: string
  closes_at: string
  duration_minutes: number
  max_attempts: number
  allow_backtracking: boolean
  shuffle_questions: boolean
  shuffle_options: boolean
  multi_answer_policy: MultiAnswerPolicy
  tab_switch_limit: number
  tab_switch_penalty_marks: number
  is_results_released: boolean
  created_at: string
  questions: Question[]
  total_questions: number
  total_marks: number
  difficulty_breakdown: DifficultyBreakdown
}

export interface QuizDetail {
  id: string
  title: string
  course_code: string
  description?: string | null
  status: QuizStatus
  created_by_id: string
  current_version_id?: string | null
  draft_version?: QuizVersion | null
  published_version?: QuizVersion | null
  is_published: boolean
  created_at: string
  updated_at: string
}

export interface PrePublishValidationError {
  field: string
  message: string
}

export interface QuizPreview {
  quiz_id: string
  version_id: string
  version_number: number
  title: string
  course_code: string
  description?: string | null
  opens_at: string
  closes_at: string
  duration_minutes: number
  max_attempts: number
  allow_backtracking: boolean
  shuffle_questions: boolean
  shuffle_options: boolean
  multi_answer_policy: MultiAnswerPolicy
  tab_switch_limit: number
  tab_switch_penalty_marks: number
  is_results_released: boolean
  total_questions: number
  total_marks: number
  difficulty_breakdown: DifficultyBreakdown
  can_publish: boolean
  validation_errors: PrePublishValidationError[]
  questions: Question[]
}

export interface PublishQuizResponse {
  success: boolean
  message: string
  quiz_id: string
  published_version_id: string
  version_number: number
}
