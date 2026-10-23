/**
 * API client for Teacher Quiz Builder, Immutable Publishing, and Assessment Settings (DEC-006, DEC-008, DEC-014).
 */
import type {
  QuizListResponse,
  QuizDetail,
  QuizCreatePayload,
  QuizUpdatePayload,
  QuizVersion,
  QuizPreview,
  PublishQuizResponse,
} from '../types/quiz'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

export async function fetchQuizzes(token: string): Promise<QuizListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(`Failed to load quizzes: HTTP ${response.status} - ${errorBody}`)
  }

  return response.json()
}

export async function createQuiz(
  token: string,
  payload: QuizCreatePayload
): Promise<QuizDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    const message = errorData?.detail
      ? typeof errorData.detail === 'string'
        ? errorData.detail
        : JSON.stringify(errorData.detail)
      : `HTTP ${response.status}`
    throw new Error(message)
  }

  return response.json()
}

export async function getQuiz(token: string, id: string): Promise<QuizDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${id}`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    throw new Error(`Quiz not found or unauthorized: HTTP ${response.status}`)
  }

  return response.json()
}

export async function updateQuiz(
  token: string,
  id: string,
  payload: QuizUpdatePayload
): Promise<QuizDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${id}`, {
    method: 'PUT',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    const message = errorData?.detail
      ? typeof errorData.detail === 'string'
        ? errorData.detail
        : JSON.stringify(errorData.detail)
      : `HTTP ${response.status}`
    throw new Error(message)
  }

  return response.json()
}

export async function addQuestionsToQuiz(
  token: string,
  quizId: string,
  questionIds: string[]
): Promise<QuizVersion> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/questions`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ question_ids: questionIds }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    const message = errorData?.detail || `HTTP ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }

  return response.json()
}

export async function removeQuestionFromQuiz(
  token: string,
  quizId: string,
  questionId: string
): Promise<QuizVersion> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/questions/${questionId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    throw new Error(`Failed to remove question: HTTP ${response.status}`)
  }

  return response.json()
}

export async function reorderQuizQuestions(
  token: string,
  quizId: string,
  questionIds: string[]
): Promise<QuizVersion> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/questions/order`, {
    method: 'PUT',
    headers: authHeaders(token),
    body: JSON.stringify({ question_ids: questionIds }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw new Error(errorData?.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export async function previewQuiz(
  token: string,
  quizId: string
): Promise<QuizPreview> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/preview`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    throw new Error(`Failed to load quiz preview: HTTP ${response.status}`)
  }

  return response.json()
}

export async function publishQuiz(
  token: string,
  quizId: string
): Promise<PublishQuizResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${quizId}/publish`, {
    method: 'POST',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    if (errorData?.detail?.errors) {
      const errorList = errorData.detail.errors.map((e: { field: string; message: string }) => `• ${e.message}`).join('\n')
      throw new Error(`Pre-publication validation failed:\n${errorList}`)
    }
    const message = errorData?.detail?.message || errorData?.detail || `HTTP ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }

  return response.json()
}
