/**
 * TypeScript definitions for Teacher Results, Grading Adjustments, and Release (DEC-010, Phase 7).
 */

export interface QuizResultSummary {
  quiz_id: string
  quiz_title: string
  course_code: string
  version_number: number
  is_published: boolean
  is_results_released: boolean
  results_released_at: string | null
  total_enrolled: number
  total_attempts: number
  submitted_count: number
  in_progress_count: number
  average_score: number | null
  highest_score: number | null
  lowest_score: number | null
  total_possible_marks: number
}

export interface AttemptListItem {
  attempt_id: string
  student_id: string
  student_name: string
  student_email: string
  student_prn: string
  student_division: string
  attempt_number: number
  status: 'in_progress' | 'submitted' | 'expired' | 'cancelled'
  started_at: string
  submitted_at: string | null
  total_score: number | null
  grading_status: 'pending' | 'auto_graded' | 'manually_adjusted'
  tab_switch_count: number
  violation_count?: number
  proctoring_deduction?: number
  is_finalized: boolean
  adjustment_count: number
}

export interface AttemptListResponse {
  items: AttemptListItem[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface QuestionOptionResult {
  id: string
  option_text: string
  order_index: number
  is_correct: boolean
}

export interface QuestionResultDetail {
  question_id: string
  prompt: string
  question_type: string
  order_index: number
  positive_marks: number
  negative_marks: number
  awarded_marks: number | null
  selected_option_ids: string[]
  options: QuestionOptionResult[]
}

export interface GradeAdjustment {
  id: string
  previous_score: number
  new_score: number
  reason: string
  adjusted_by_name: string
  created_at: string
}

export interface TelemetryEvent {
  id: string
  event_type: string
  client_event_id?: string | null
  event_timestamp: string
  event_data: Record<string, unknown> | null
}

export interface EffectiveProctoringPolicy {
  version_number?: number
  free_allowance?: number
  deduction_per_violation?: number
  max_deduction?: number
  enable_copy_paste_restriction?: boolean
  count_copy_paste_violations?: boolean
  require_fullscreen?: boolean
  count_fullscreen_exit_violations?: boolean
  count_tab_switch_violations?: boolean
  count_dev_tools_violations?: boolean
  enable_proctoring_warnings?: boolean
}

export interface AttemptDetail {
  attempt_id: string
  quiz_id: string
  quiz_title: string
  course_code: string
  version_number: number
  student_name: string
  student_email: string
  student_prn: string
  student_division: string
  attempt_number: number
  status: string
  started_at: string
  submitted_at: string | null
  deadline_at: string
  total_score: number | null
  max_possible_marks: number
  grading_status: string
  tab_switch_count: number
  violation_count?: number
  proctoring_deduction?: number
  effective_policy?: EffectiveProctoringPolicy
  violation_breakdown?: Record<string, number>
  is_finalized: boolean
  questions: QuestionResultDetail[]
  adjustments: GradeAdjustment[]
  telemetry_events: TelemetryEvent[]
}

export interface GradeAdjustmentRequest {
  new_score: number
  reason: string
}

export interface ReleaseResultsResponse {
  quiz_id: string
  version_number: number
  is_results_released: boolean
  results_released_at: string
  message: string
}

export interface StudentAttemptResult {
  attempt_id: string
  quiz_id: string
  quiz_title: string
  course_code: string
  attempt_number: number
  status: string
  started_at: string
  submitted_at: string | null
  total_score: number
  max_possible_score: number
  grading_status: string
  tab_switch_count: number
  is_results_released: boolean
}
