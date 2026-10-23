/**
 * API client for Teacher Student Roster & Assessment Assignments (DEC-007, Phase 5).
 */
import type {
  AssignmentListResponse,
  Assignment,
  AssignmentCreateRequest,
  RosterPreviewResponse,
  RosterImportSummaryResponse,
  StudentEligibilityResponse,
} from '../types/roster'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

export async function fetchAssignments(
  token: string,
  quizId: string,
  params?: {
    search?: string
    division?: string
    is_active?: boolean
    page?: number
    page_size?: number
  }
): Promise<AssignmentListResponse> {
  const url = new URL(`${API_BASE_URL}/api/v1/quizzes/${quizId}/assignments`)
  if (params?.search) url.searchParams.set('search', params.search)
  if (params?.division) url.searchParams.set('division', params.division)
  if (params?.is_active !== undefined) url.searchParams.set('is_active', String(params.is_active))
  if (params?.page) url.searchParams.set('page', String(params.page))
  if (params?.page_size) url.searchParams.set('page_size', String(params.page_size))

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(`Failed to fetch assignments: ${response.status} - ${errorBody}`)
  }

  return response.json()
}

export async function previewRosterUpload(
  token: string,
  quizId: string,
  file: File
): Promise<RosterPreviewResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/roster/preview`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(`Roster preview failed: ${response.status} - ${errorBody}`)
  }

  return response.json()
}

export async function confirmRosterImport(
  token: string,
  quizId: string,
  file: File
): Promise<RosterImportSummaryResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/roster/import`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    let message = `Roster import failed with status ${response.status}`
    try {
      const errorJson = await response.json()
      if (errorJson.detail?.message) {
        message = errorJson.detail.message
      } else if (typeof errorJson.detail === 'string') {
        message = errorJson.detail
      }
    } catch {
      // Fallback
    }
    throw new Error(message)
  }

  return response.json()
}

export async function addSingleAssignment(
  token: string,
  quizId: string,
  payload: AssignmentCreateRequest
): Promise<Assignment> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/assignments`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = `Failed to add student: ${response.status}`
    try {
      const errorJson = await response.json()
      if (errorJson.detail) message = errorJson.detail
    } catch {
      // Fallback
    }
    throw new Error(message)
  }

  return response.json()
}

export async function updateAssignmentStatus(
  token: string,
  quizId: string,
  assignmentId: string,
  isActive: boolean
): Promise<Assignment> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/quizzes/${quizId}/assignments/${assignmentId}/status`,
    {
      method: 'PATCH',
      headers: authHeaders(token),
      body: JSON.stringify({ is_active: isActive }),
    }
  )

  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(`Failed to update assignment status: ${response.status} - ${errorBody}`)
  }

  return response.json()
}

export async function deleteAssignment(
  token: string,
  quizId: string,
  assignmentId: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/quizzes/${quizId}/assignments/${assignmentId}`,
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )

  if (!response.ok) {
    let message = `Failed to delete assignment: ${response.status}`
    try {
      const errorJson = await response.json()
      if (errorJson.detail) message = errorJson.detail
    } catch {
      // Fallback
    }
    throw new Error(message)
  }
}

export async function downloadRosterTemplate(
  token: string,
  quizId: string,
  format: 'csv' | 'xlsx'
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/quizzes/${quizId}/roster/template?format=${format}`,
    {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to download template: ${response.status}`)
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `student_roster_template.${format}`
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

export async function fetchStudentEligibility(
  token: string,
  quizId: string
): Promise<StudentEligibilityResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/student/quizzes/${quizId}/eligibility`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    let message = `Eligibility check failed: ${response.status}`
    try {
      const errorJson = await response.json()
      if (errorJson.detail) message = errorJson.detail
    } catch {
      // Fallback
    }
    throw new Error(message)
  }

  return response.json()
}
