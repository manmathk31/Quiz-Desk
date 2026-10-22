/**
 * Types and interfaces for Teacher Question Bank & CSV Import (DEC-006).
 */

export type QuestionType = 'single_choice' | 'multiple_choice' | 'true_false'

export interface QuestionOption {
  id: string
  option_text: string
  order_index: number
  is_correct: boolean
}

export interface QuestionOptionInput {
  option_text: string
  order_index: number
  is_correct: boolean
}

export interface Question {
  id: string
  created_by_id: string | null
  question_type: QuestionType
  prompt: string
  positive_marks: number
  negative_marks: number
  options: QuestionOption[]
  created_at: string
  updated_at: string
}

export interface QuestionListResponse {
  items: Question[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface QuestionCreatePayload {
  question_type: QuestionType
  prompt: string
  positive_marks: number
  negative_marks: number
  options: QuestionOptionInput[]
}

export interface CSVRowError {
  row_number: number
  column?: string | null
  message: string
}

export interface ParsedOption {
  option_text: string
  order_index: number
  is_correct: boolean
}

export interface ParsedQuestion {
  row_number: number
  question_type: QuestionType
  prompt: string
  positive_marks: number
  negative_marks: number
  options: ParsedOption[]
}

export interface CSVPreviewResponse {
  is_valid: boolean
  total_rows: number
  valid_count: number
  error_count: number
  questions: ParsedQuestion[]
  errors: CSVRowError[]
}

export interface CSVImportResponse {
  success: boolean
  imported_count: number
  message: string
  question_ids: string[]
}
