/**
 * API client for Admin Portal, User Management, Audit Logs, and Guarded Reset (DEC-022).
 */
import type {
  AdminAuditLogResponse,
  AdminCleanWorkspaceResponse,
  AdminDestructiveResetResponse,
  AdminOverviewResponse,
  AdminResetStatusResponse,
  AdminTeacherCreateRequest,
  AdminUserListItem,
  AdminUserListResponse,
  AdminUserPurgeRequest,
  AdminUserPurgeResponse,
} from '../types/admin'
import type { UserProfile } from '../types/auth'


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

async function handleResponse<T>(res: Response, fallbackMessage: string): Promise<T> {
  if (!res.ok) {
    let errorDetail = `${fallbackMessage} (HTTP ${res.status})`
    try {
      const err = await res.json()
      if (err.detail) {
        errorDetail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)
      }
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }
  return res.json()
}

export async function fetchAdminOverview(token: string): Promise<AdminOverviewResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/overview`, {
    method: 'GET',
    headers: authHeaders(token),
  })
  return handleResponse<AdminOverviewResponse>(response, 'Failed to fetch admin overview metrics')
}

export async function fetchAdminUsers(
  token: string,
  page = 1,
  pageSize = 20,
  search?: string,
  role?: string
): Promise<AdminUserListResponse> {
  const params = new URLSearchParams()
  params.append('page', page.toString())
  params.append('page_size', pageSize.toString())
  if (search && search.trim()) params.append('search', search.trim())
  if (role && role !== 'all') params.append('role', role)

  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users?${params.toString()}`, {
    method: 'GET',
    headers: authHeaders(token),
  })
  return handleResponse<AdminUserListResponse>(response, 'Failed to fetch user directory')
}

export async function updateAdminUserStatus(
  token: string,
  userId: string,
  isActive: boolean
): Promise<AdminUserListItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users/${userId}/status`, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify({ is_active: isActive }),
  })
  return handleResponse<AdminUserListItem>(response, 'Failed to update user account status')
}

export async function fetchAdminAuditLogs(
  token: string,
  page = 1,
  pageSize = 20,
  action?: string
): Promise<AdminAuditLogResponse> {
  const params = new URLSearchParams()
  params.append('page', page.toString())
  params.append('page_size', pageSize.toString())
  if (action && action.trim()) params.append('action', action.trim())

  const response = await fetch(`${API_BASE_URL}/api/v1/admin/audit-logs?${params.toString()}`, {
    method: 'GET',
    headers: authHeaders(token),
  })
  return handleResponse<AdminAuditLogResponse>(response, 'Failed to fetch audit log trail')
}

export async function fetchResetStatus(token: string): Promise<AdminResetStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/reset-status`, {
    method: 'GET',
    headers: authHeaders(token),
  })
  return handleResponse<AdminResetStatusResponse>(response, 'Failed to check reset status')
}

export async function executeDestructiveReset(
  token: string,
  confirmationCode: string
): Promise<AdminDestructiveResetResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/reset-test-data`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ confirmation_code: confirmationCode }),
  })
  return handleResponse<AdminDestructiveResetResponse>(response, 'Destructive reset execution failed')
}

export async function bootstrapAdminUser(
  token: string,
  bootstrapToken?: string
): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/bootstrap`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ bootstrap_token: bootstrapToken || undefined }),
  })
  return handleResponse<UserProfile>(response, 'Administrator initial bootstrap failed')
}

export async function createAdminTeacher(
  token: string,
  payload: AdminTeacherCreateRequest
): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/teachers`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
  return handleResponse<UserProfile>(response, 'Failed to create faculty account')
}

export async function purgeAdminUser(
  token: string,
  payload: AdminUserPurgeRequest
): Promise<AdminUserPurgeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users/purge`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
  return handleResponse<AdminUserPurgeResponse>(response, 'Failed to purge user account')
}

export async function executeCleanTeacherWorkspace(
  token: string,
  confirmationCode: string
): Promise<AdminCleanWorkspaceResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/clean-teacher-workspace`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ confirmation_code: confirmationCode }),
  })
  return handleResponse<AdminCleanWorkspaceResponse>(response, 'Failed to execute clean workspace reset')
}

