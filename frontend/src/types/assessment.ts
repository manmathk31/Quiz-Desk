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
  tab_switch_penalty_marks?: number
  tab_switch_penalty?: number
  violation_count?: number
  free_violation_allowance?: number
  violation_penalty_marks?: number
  max_proctoring_deduction?: number
  current_proctoring_deduction?: number
  proctoring_deduction?: number
  enable_copy_paste_restriction?: boolean
  count_copy_paste_violations?: boolean
  require_fullscreen?: boolean
  count_fullscreen_exit_violations?: boolean
  count_tab_switch_violations?: boolean
  count_dev_tools_violations?: boolean
  enable_proctoring_warnings?: boolean
  allow_backtracking: boolean
  questions: SanitizedQuestion[]
}

export interface AssessmentReadiness {
  quiz_id: string
  quiz_title: string
  course_code: string
  description?: string | null
  opens_at: string
  closes_at: string
  duration_minutes: number
  max_attempts: number
  attempts_taken: number
  allow_backtracking: boolean
  free_violation_allowance: number
  violation_penalty_marks: number
  max_proctoring_deduction: number
  enable_copy_paste_restriction: boolean
  count_copy_paste_violations: boolean
  require_fullscreen: boolean
  count_fullscreen_exit_violations: boolean
  count_tab_switch_violations: boolean
  count_dev_tools_violations: boolean
  enable_proctoring_warnings: boolean
  has_active_attempt: boolean
  active_attempt_id?: string | null
  can_start: boolean
  status_message: string
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
  client_event_id?: string
  client_timestamp?: string
  event_data?: Record<string, unknown> | null
}

export interface TelemetryEventResponse {
  tab_switch_count: number
  violation_count?: number
  free_allowance?: number
  remaining_free_violations?: number
  chargeable_violations?: number
  current_deduction?: number
  proctoring_deduction?: number
  limit_exceeded: boolean
  tab_switch_limit: number
  warning_message?: string | null
  message?: string | null
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
