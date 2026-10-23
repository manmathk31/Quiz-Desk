import React, { useState, useRef } from 'react'
import type { CSVPreviewResponse } from '../../types/question'
import {
  previewQuestionCsv,
  importQuestionCsv,
  downloadCsvTemplate,
} from '../../services/questionBankApi'
import {
  X,
  Upload,
  Download,
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  AlertTriangle,
} from 'lucide-react'

interface CsvImportModalProps {
  isOpen: boolean
  token: string
  onClose: () => void
  onImportSuccess: () => void
}

export const CsvImportModal: React.FC<CsvImportModalProps> = ({
  isOpen,
  token,
  onClose,
  onImportSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewResult, setPreviewResult] = useState<CSVPreviewResponse | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [importSuccessMessage, setImportSuccessMessage] = useState<string | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setSelectedFile(file)
    setPreviewResult(null)
    setImportSuccessMessage(null)
    setGeneralError(null)

    // Run preview validation immediately
    setIsValidating(true)
    try {
      const result = await previewQuestionCsv(token, file)
      setPreviewResult(result)
    } catch (err: unknown) {
      setGeneralError(err instanceof Error ? err.message : 'Failed to parse CSV file.')
    } finally {
      setIsValidating(false)
    }
  }

  const handleDownloadTemplate = async () => {
    try {
      await downloadCsvTemplate(token)
    } catch (err: unknown) {
      setGeneralError(err instanceof Error ? err.message : 'Failed to download template.')
    }
  }

  const handleConfirmImport = async () => {
    if (!selectedFile || !previewResult?.is_valid) return

    setIsImporting(true)
    setGeneralError(null)
    try {
      const res = await importQuestionCsv(token, selectedFile)
      setImportSuccessMessage(res.message)
      onImportSuccess()
      setTimeout(() => {
        handleResetAndClose()
      }, 1500)
    } catch (err: unknown) {
      setGeneralError(err instanceof Error ? err.message : 'Import failed.')
    } finally {
      setIsImporting(false)
    }
  }

  const handleResetAndClose = () => {
    setSelectedFile(null)
    setPreviewResult(null)
    setImportSuccessMessage(null)
    setGeneralError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-3xl w-full max-h-[92vh] flex flex-col text-slate-900">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
              <Upload className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Import Questions from CSV or Excel</h2>
              <p className="text-xs text-slate-500">
                Bulk import reusable questions with preview, difficulty detection, and error checking
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleResetAndClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {generalError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{generalError}</span>
            </div>
          )}

          {importSuccessMessage && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <span className="font-semibold">{importSuccessMessage}</span>
            </div>
          )}

          {/* Template helper box */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-5 h-5 text-slate-500" />
              <div>
                <p className="text-xs font-semibold text-slate-800">Need the standard spreadsheet format?</p>
                <p className="text-[11px] text-slate-500">
                  Headers: question_type, difficulty, question_text, option_a, option_b, option_c, option_d, correct_answers, positive_marks, negative_marks
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleDownloadTemplate}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-medium transition-colors shrink-0"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Template</span>
            </button>
          </div>

          {/* File Upload Zone */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Select Question Spreadsheet (CSV or .xlsx, Max 2MB, up to 200 questions)
            </label>
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-blue-50/20"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={handleFileChange}
                className="hidden"
              />
              <Upload className="w-8 h-8 mx-auto text-slate-400 mb-2" />
              {selectedFile ? (
                <div>
                  <p className="text-xs font-semibold text-slate-800">{selectedFile.name}</p>
                  <p className="text-[11px] text-slate-500">
                    {(selectedFile.size / 1024).toFixed(1)} KB — Click to change file
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-medium text-slate-700">
                    Click to select or drag and drop your CSV or Excel (.xlsx) file here
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">Supports UTF-8 CSV and genuine Excel (.xlsx) workbooks</p>
                </div>
              )}
            </div>
          </div>

          {/* Validation In-Progress */}
          {isValidating && (
            <div className="p-6 text-center space-y-2">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600 mx-auto" />
              <p className="text-xs text-slate-600 font-medium">
                Validating questions, options, and answer keys...
              </p>
            </div>
          )}

          {/* Validation Preview Results */}
          {previewResult && !isValidating && (
            <div className="space-y-4">
              {/* Summary Stats Header */}
              <div className="flex flex-wrap items-center gap-3">
                <div
                  className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center space-x-1.5 ${
                    previewResult.is_valid
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {previewResult.is_valid ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Validation Passed</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>Validation Failed ({previewResult.error_count} errors)</span>
                    </>
                  )}
                </div>

                <span className="text-xs text-slate-500">
                  Total Rows: <strong className="text-slate-800">{previewResult.total_rows}</strong>
                </span>
                <span className="text-xs text-emerald-600">
                  Valid Questions: <strong>{previewResult.valid_count}</strong>
                </span>
                {previewResult.error_count > 0 && (
                  <span className="text-xs text-rose-600 font-medium">
                    Errors: <strong>{previewResult.error_count}</strong>
                  </span>
                )}
              </div>

              {/* Error Details Table (if any errors exist) */}
              {previewResult.error_count > 0 && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-xs space-y-2">
                  <div className="flex items-center space-x-2 text-rose-900 font-semibold">
                    <AlertCircle className="w-4 h-4 text-rose-600" />
                    <span>Correction Required Before Import (All-or-Nothing Rule)</span>
                  </div>
                  <p className="text-[11px] text-rose-700">
                    To prevent corrupt data, Quizdesk enforces all-or-nothing imports. Please fix the following row errors in your CSV:
                  </p>
                  <div className="max-h-40 overflow-y-auto space-y-1.5 pt-2">
                    {previewResult.errors.map((err, idx) => (
                      <div
                        key={idx}
                        className="p-2 bg-white rounded border border-rose-200 text-slate-800 font-mono text-[11px] flex justify-between"
                      >
                        <span className="font-bold text-rose-800">
                          Row {err.row_number} {err.column ? `[${err.column}]` : ''}:
                        </span>
                        <span className="text-slate-700 ml-2 text-right">{err.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Questions Preview Table */}
              {previewResult.questions.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                    Parsed Questions Preview ({previewResult.questions.length})
                  </h3>
                  <div className="border border-slate-200 rounded-lg overflow-hidden max-h-56 overflow-y-auto">
                    <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                      <thead className="bg-slate-50 text-slate-600 font-semibold sticky top-0">
                        <tr>
                          <th className="px-3 py-2">Row</th>
                          <th className="px-3 py-2">Type</th>
                          <th className="px-3 py-2">Prompt</th>
                          <th className="px-3 py-2">Options</th>
                          <th className="px-3 py-2">Marks</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {previewResult.questions.map((q) => (
                          <tr key={q.row_number} className="hover:bg-slate-50/60">
                            <td className="px-3 py-2 text-slate-500 font-mono">{q.row_number}</td>
                            <td className="px-3 py-2 whitespace-nowrap">
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                                {q.question_type.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="px-3 py-2 max-w-xs truncate font-medium text-slate-800" title={q.prompt}>
                              {q.prompt}
                            </td>
                            <td className="px-3 py-2 max-w-xs truncate text-slate-600">
                              {q.options
                                .map((o) => `${o.option_text}${o.is_correct ? ' (✓)' : ''}`)
                                .join(' | ')}
                            </td>
                            <td className="px-3 py-2 whitespace-nowrap text-slate-600 font-mono">
                              +{q.positive_marks} / -{q.negative_marks}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-xl flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {previewResult?.is_valid
              ? `Ready to import ${previewResult.valid_count} questions.`
              : 'Valid CSV required to enable import.'}
          </span>
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleResetAndClose}
              disabled={isImporting}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 rounded-lg hover:bg-slate-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmImport}
              disabled={!previewResult?.is_valid || isImporting || isValidating}
              className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-xs"
            >
              {isImporting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Importing Batch...</span>
                </>
              ) : (
                <span>Confirm & Import ({previewResult?.valid_count || 0})</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
