/**
 * API client for Student Assessments, Delivery, Autosave, Telemetry, and Submission (DEC-008, DEC-009, DEC-010).
 */
import type {
  StudentQuizListResponse,
  AttemptStartResponse,
  AttemptContent,
  AssessmentReadiness,
  AnswerSaveRequest,
  AnswerSaveResponse,
  TelemetryEventRequest,
  TelemetryEventResponse,
  AttemptSubmissionResponse,
} from '../types/assessment'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

export async function fetchStudentQuizzes(token: string): Promise<StudentQuizListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/student/quizzes`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(`Failed to load student assessments: ${response.status} - ${errorBody}`)
  }

  return response.json()
}

export async function fetchAssessmentReadiness(
  token: string,
  quizId: string
): Promise<AssessmentReadiness> {
  const response = await fetch(`${API_BASE_URL}/api/v1/student/quizzes/${quizId}/readiness`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    let errorDetail = `Failed to load readiness information (${response.status})`
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

export async function startOrResumeAttempt(
  token: string,
  quizId: string
): Promise<AttemptStartResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/student/quizzes/${quizId}/attempts`, {
    method: 'POST',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    let errorDetail = `Failed to start assessment (${response.status})`
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

export async function fetchAttemptContent(
  token: string,
  attemptId: string
): Promise<AttemptContent> {
  const response = await fetch(`${API_BASE_URL}/api/v1/student/attempts/${attemptId}`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    let errorDetail = `Failed to load assessment content (${response.status})`
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

export async function autosaveAnswer(
  token: string,
  attemptId: string,
  questionId: string,
  payload: AnswerSaveRequest
): Promise<AnswerSaveResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/student/attempts/${attemptId}/answers/${questionId}`,
    {
      method: 'PUT',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    }
  )

  if (!response.ok) {
    let errorDetail = `Failed to save answer (${response.status})`
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

export async function sendTelemetry(
  token: string,
  attemptId: string,
  payload: TelemetryEventRequest
): Promise<TelemetryEventResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/student/attempts/${attemptId}/telemetry`,
    {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    }
  )

  if (!response.ok) {
    let errorDetail = `Telemetry recording failed (${response.status})`
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

export async function submitAttempt(
  token: string,
  attemptId: string
): Promise<AttemptSubmissionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/student/attempts/${attemptId}/submit`, {
    method: 'POST',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    let errorDetail = `Failed to submit assessment (${response.status})`
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
