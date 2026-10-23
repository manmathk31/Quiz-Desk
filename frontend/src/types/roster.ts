/**
 * Student Roster and Assessment Eligibility types (DEC-007, Phase 5).
 */

export interface RosterRowError {
  row_number: number
  column?: string | null
  message: string
}

export interface RosterPreviewItem {
  row_number: number
  prn: string
  name: string
  email: string
  division: string
  assignment_status: 'new' | 'already_assigned' | 'conflict'

  match_status: 'matched' | 'unregistered' | 'pending_profile' | 'conflict'
  matched_user_id?: string | null
  conflict_reason?: string | null
  is_currently_active?: boolean | null
}

export interface RosterPreviewResponse {
  total_rows: number
  valid_rows: number
  new_assignments_count: number
  already_assigned_count: number
  conflicts_count: number
  matched_count: number
  unregistered_count: number
  pending_profile_count: number
  can_confirm: boolean
  items: RosterPreviewItem[]
  errors: RosterRowError[]
}

export interface RosterImportSummaryResponse {
  imported_count: number
  already_assigned_count: number
  matched_accounts_count: number
  unregistered_count: number
  message: string
}

export interface Assignment {
  id: string
  quiz_id: string
  student_prn: string
  student_name: string
  student_email: string
  division: string
  assigned_student_id?: string | null
  is_active: boolean
  created_at: string
  revoked_at?: string | null
  match_status: 'matched' | 'unregistered'
  has_attempts: boolean
}

export interface AssignmentSummaryStats {
  total_assigned: number
  active_count: number
  revoked_count: number
  matched_count: number
  unregistered_count: number
  divisions: string[]
}

export interface AssignmentListResponse {
  items: Assignment[]
  total_count: number
  page: number
  page_size: number
  summary: AssignmentSummaryStats
}

export interface AssignmentCreateRequest {
  prn: string
  name: string
  email: string
  division: string
}

export interface StudentEligibilityResponse {
  is_eligible: boolean
  quiz_id: string
  quiz_title: string
  course_code: string
  quiz_version_id: string
  version_number: number
  assignment_id: string
  student_prn: string
  student_name: string
  student_email: string
  division: string
  opens_at: string
  closes_at: string
  duration_minutes: number
  max_attempts: number
  is_open: boolean
  status_message: string
}
