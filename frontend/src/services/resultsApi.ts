/**
 * API client for Teacher Assessment Results, Grade Adjustments, and Release (DEC-010, Phase 7).
 */
import type {
  QuizResultSummary,
  AttemptListResponse,
  AttemptDetail,
  GradeAdjustmentRequest,
  ReleaseResultsResponse,
  StudentAttemptResult,
} from '../types/results'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

export async function fetchQuizResultSummary(
  token: string,
  quizId: string
): Promise<QuizResultSummary> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/results/summary`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    let errorDetail = `Failed to load assessment summary (${response.status})`
    try {
      const err = await response.json()
      if (err.detail) errorDetail = err.detail
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export async function fetchQuizAttempts(
  token: string,
  quizId: string,
  page = 1,
  limit = 20,
  status?: string,
  search?: string
): Promise<AttemptListResponse> {
  const params = new URLSearchParams()
  params.append('page', page.toString())
  params.append('limit', limit.toString())
  if (status && status !== 'all') params.append('status', status)
  if (search && search.trim()) params.append('search', search.trim())

  const response = await fetch(
    `${API_BASE_URL}/api/v1/quizzes/${quizId}/results/attempts?${params.toString()}`,
    {
      method: 'GET',
      headers: authHeaders(token),
    }
  )

  if (!response.ok) {
    let errorDetail = `Failed to load assessment attempts (${response.status})`
    try {
      const err = await response.json()
      if (err.detail) errorDetail = err.detail
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export async function fetchAttemptDetail(
  token: string,
  quizId: string,
  attemptId: string
): Promise<AttemptDetail> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/quizzes/${quizId}/results/attempts/${attemptId}`,
    {
      method: 'GET',
      headers: authHeaders(token),
    }
  )

  if (!response.ok) {
    let errorDetail = `Failed to load attempt details (${response.status})`
    try {
      const err = await response.json()
      if (err.detail) errorDetail = err.detail
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export async function adjustAttemptScore(
  token: string,
  quizId: string,
  attemptId: string,
  payload: GradeAdjustmentRequest
): Promise<AttemptDetail> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/quizzes/${quizId}/results/attempts/${attemptId}/adjust`,
    {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    }
  )

  if (!response.ok) {
    let errorDetail = `Failed to adjust score (${response.status})`
    try {
      const err = await response.json()
      if (err.detail) errorDetail = err.detail
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export async function releaseQuizResults(
  token: string,
  quizId: string
): Promise<ReleaseResultsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/results/release`, {
    method: 'POST',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    let errorDetail = `Failed to release results (${response.status})`
    try {
      const err = await response.json()
      if (err.detail) errorDetail = err.detail
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export async function downloadQuizResultsCsv(token: string, quizId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/results/export`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let errorDetail = `Failed to export CSV (${response.status})`
    try {
      const err = await response.json()
      if (err.detail) errorDetail = err.detail
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }

  return response.blob()
}

export async function fetchStudentAttemptResult(
  token: string,
  attemptId: string
): Promise<StudentAttemptResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/student/attempts/${attemptId}/result`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    let errorDetail = `Failed to retrieve assessment score (${response.status})`
    try {
      const err = await response.json()
      if (err.detail) errorDetail = err.detail
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }

  return response.json()
}
