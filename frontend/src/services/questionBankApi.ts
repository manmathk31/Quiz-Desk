/**
 * API client for Teacher Question Bank and CSV Import operations (DEC-006).
 */
import type {
  Question,
  QuestionListResponse,
  QuestionCreatePayload,
  CSVPreviewResponse,
  CSVImportResponse,
} from '../types/question'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
  }
}

export async function fetchQuestionBank(
  token: string,
  params: {
    page?: number
    page_size?: number
    question_type?: string
    search?: string
  } = {}
): Promise<QuestionListResponse> {
  const query = new URLSearchParams()
  if (params.page) query.set('page', params.page.toString())
  if (params.page_size) query.set('page_size', params.page_size.toString())
  if (params.question_type) query.set('question_type', params.question_type)
  if (params.search) query.set('search', params.search)

  const url = `${API_BASE_URL}/api/v1/question-bank?${query.toString()}`
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      ...authHeaders(token),
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(`Failed to fetch questions: HTTP ${response.status} - ${errorBody}`)
  }

  return response.json()
}

export async function createQuestion(
  token: string,
  payload: QuestionCreatePayload
): Promise<Question> {
  const response = await fetch(`${API_BASE_URL}/api/v1/question-bank`, {
    method: 'POST',
    headers: {
      ...authHeaders(token),
      'Content-Type': 'application/json',
    },
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

export async function updateQuestion(
  token: string,
  id: string,
  payload: QuestionCreatePayload
): Promise<Question> {
  const response = await fetch(`${API_BASE_URL}/api/v1/question-bank/${id}`, {
    method: 'PUT',
    headers: {
      ...authHeaders(token),
      'Content-Type': 'application/json',
    },
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

export async function deleteQuestion(token: string, id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/question-bank/${id}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })

  if (!response.ok && response.status !== 204) {
    throw new Error(`Failed to delete question: HTTP ${response.status}`)
  }
}

export async function previewQuestionCsv(
  token: string,
  file: File
): Promise<CSVPreviewResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/question-bank/csv/preview`, {
    method: 'POST',
    headers: authHeaders(token),
    body: formData,
  })

  if (!response.ok) {
    const errText = await response.text()
    throw new Error(`CSV preview failed: HTTP ${response.status} - ${errText}`)
  }

  return response.json()
}

export async function importQuestionCsv(
  token: string,
  file: File
): Promise<CSVImportResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/question-bank/csv/import`, {
    method: 'POST',
    headers: authHeaders(token),
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    if (errorData?.detail?.errors) {
      throw new Error(
        `Import failed with ${errorData.detail.error_count} error(s). Please review preview.`
      )
    }
    const message = errorData?.detail?.message || errorData?.detail || `HTTP ${response.status}`
    throw new Error(message)
  }

  return response.json()
}

export async function downloadCsvTemplate(token: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/question-bank/csv/template`, {
    method: 'GET',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    throw new Error(`Failed to download template: HTTP ${response.status}`)
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'quizdesk_question_bank_template.csv'
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}
