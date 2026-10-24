/**
 * Type definitions for Admin Portal and operational endpoints (DEC-022).
 */
import type { UserRole } from './auth'

export interface AdminOverviewStats {
  total_students: number
  total_teachers: number
  total_quizzes: number
  published_quizzes: number
  active_attempts: number
  total_attempts: number
}

export interface AdminActivityItem {
  id: string
  action: string
  entity_type: string
  entity_id: string
  user_email: string | null
  created_at: string
}

export interface AdminOverviewResponse {
  stats: AdminOverviewStats
  recent_activity: AdminActivityItem[]
}

export interface AdminUserListItem {
  id: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
  prn: string | null
  division: string | null
  created_at: string
}

export interface AdminUserListResponse {
  total: number
  items: AdminUserListItem[]
  page: number
  page_size: number
}

export interface AdminAuditLogItem {
  id: string
  action: string
  entity_type: string
  entity_id: string
  user_id: string | null
  user_email: string | null
  details: unknown
  ip_address: string | null
  created_at: string
}

export interface AdminAuditLogResponse {
  total: number
  items: AdminAuditLogItem[]
  page: number
  page_size: number
}

export interface AdminResetStatusResponse {
  allow_destructive_reset: boolean
  environment: string
  can_reset: boolean
  warning_notice: string
}

export interface AdminDestructiveResetResponse {
  success: boolean
  message: string
  cleared_records: Record<string, number>
  executed_at: string
}

export interface AdminTeacherCreateRequest {
  email: string
  name: string
  password: string
}

export interface AdminStudentCreateRequest {
  email: string
  name: string
  prn: string
  division?: string
  password: string
}

export interface AdminUserPurgeRequest {
  target_email: string
  admin_password: string
}

export interface AdminUserPurgeResponse {
  success: boolean
  message: string
  purged_user_id: string
  purged_email: string
  cleared_records: Record<string, number>
  executed_at: string
}

export interface AdminCleanWorkspaceResponse {
  success: boolean
  message: string
  cleared_records: Record<string, number>
  purged_students_count: number
  preserved_teachers_count: number
  executed_at: string
}

