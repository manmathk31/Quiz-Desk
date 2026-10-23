/**
 * Student Active Assessment, Autosave, Telemetry, and Submission types (DEC-008, DEC-009, DEC-010).
 */

export interface StudentQuizSummary {
  quiz_id: string
  quiz_title: string
  course_code: string
  description?: string | null
  opens_at: string
  closes_at: string
  duration_minutes: number
  max_attempts: number
  attempts_taken: number
  active_attempt_id?: string | null
  availability_status: 'UPCOMING' | 'OPEN' | 'CLOSED' | 'COMPLETED'
  status_message: string
}

export interface StudentQuizListResponse {
  items: StudentQuizSummary[]
  total: number
}

export interface AttemptStartResponse {
  attempt_id: string
  quiz_id: string
  quiz_version_id: string
  attempt_number: number
  status: 'in_progress' | 'submitted' | 'expired' | 'cancelled'
  started_at: string
  deadline_at: string
  remaining_seconds: number
  is_resumed: boolean
}

export interface SanitizedOption {
  id: string
  option_text: string
  order_index: number
}

export interface SavedAnswer {
  selected_option_ids: string[]
  is_marked_for_review: boolean
  saved_at: string
}

export interface SanitizedQuestion {
  id: string
  prompt: string
  question_type: 'single_choice' | 'multiple_choice' | 'true_false'
  order_index: number
  positive_marks: number
  negative_marks: number
  options: SanitizedOption[]
  saved_answer?: SavedAnswer | null
}

export interface AttemptContent {
  attempt_id: string
  quiz_id: string
  quiz_title: string
  course_code: string
  status: 'in_progress' | 'submitted' | 'expired' | 'cancelled'
  started_at: string
  deadline_at: string
  server_time: string
  remaining_seconds: number
  is_finalized: boolean
  tab_switch_count: number
  tab_switch_limit: number
  allow_backtracking: boolean
  questions: SanitizedQuestion[]
}

export interface AnswerSaveRequest {
  selected_option_ids: string[]
  is_marked_for_review?: boolean
  client_timestamp?: string
}

export interface AnswerSaveResponse {
  success: boolean
  saved_at: string
  is_marked_for_review: boolean
  selected_option_ids: string[]
}

export interface TelemetryEventRequest {
  event_type: string
  event_data?: Record<string, unknown> | null
}

export interface TelemetryEventResponse {
  tab_switch_count: number
  limit_exceeded: boolean
  tab_switch_limit: number
}

export interface AttemptSubmissionResponse {
  attempt_id: string
  status: 'submitted' | 'expired'
  submitted_at: string
  is_finalized: boolean
  total_score?: number | null
  is_results_released: boolean
  message: string
}
