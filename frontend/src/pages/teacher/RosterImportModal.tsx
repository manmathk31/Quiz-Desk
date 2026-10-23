import React, { useState, useRef } from 'react'
import {
  X,
  Upload,
  FileSpreadsheet,
  Download,
  AlertCircle,
  CheckCircle2,
  Users,
  AlertTriangle,
  ArrowLeft,
  FileText,
} from 'lucide-react'
import {
  previewRosterUpload,
  confirmRosterImport,
  downloadRosterTemplate,
} from '../../services/rosterApi'
import type { RosterPreviewResponse, RosterImportSummaryResponse } from '../../types/roster'

interface RosterImportModalProps {
  isOpen: boolean
  onClose: () => void
  quizId: string
  token: string
  onImportSuccess: () => void
}

export const RosterImportModal: React.FC<RosterImportModalProps> = ({
  isOpen,
  onClose,
  quizId,
  token,
  onImportSuccess,
}) => {
  const [stage, setStage] = useState<'upload' | 'preview' | 'success'>('upload')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<RosterPreviewResponse | null>(null)
  const [importSummary, setImportSummary] = useState<RosterImportSummaryResponse | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setSelectedFile(file)
      setError(null)
    }
  }

  const handlePreview = async () => {
    if (!selectedFile) {
      setError('Please select a CSV or Excel file to preview.')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      const result = await previewRosterUpload(token, quizId, selectedFile)
      setPreviewData(result)
      setStage('preview')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to preview roster file.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleConfirmImport = async () => {
    if (!selectedFile) return

    setIsProcessing(true)
    setError(null)

    try {
      const summary = await confirmRosterImport(token, quizId, selectedFile)
      setImportSummary(summary)
      setStage('success')
      onImportSuccess()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to commit roster import.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDownloadTemplate = async (format: 'csv' | 'xlsx') => {
    try {
      await downloadRosterTemplate(token, quizId, format)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to download template.')
    }
  }

  const handleClose = () => {
    setStage('upload')
    setSelectedFile(null)
    setPreviewData(null)
    setImportSummary(null)
    setError(null)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-slate-800">
              {stage === 'upload' && 'Upload Student Roster'}
              {stage === 'preview' && 'Roster Validation & Identity Preview'}
              {stage === 'success' && 'Roster Import Complete'}
            </h3>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>


        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {error && (
            <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2.5 text-sm text-rose-700">
              <AlertCircle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
              <div>
                <p className="font-medium">Import Issue Detected</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {/* STAGE 1: UPLOAD */}
          {stage === 'upload' && (
            <div className="space-y-6">
              <div
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                  selectedFile
                    ? 'border-blue-500 bg-blue-50/40'
                    : 'border-slate-300 hover:border-blue-400 bg-slate-50/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="mx-auto w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mb-3">
                  <Upload className="w-6 h-6" />
                </div>
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{selectedFile.name}</p>
                    <p className="text-xs text-slate-500 mt-1">
                      {(selectedFile.size / 1024).toFixed(1)} KB — Click to change file
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-semibold text-slate-700">
                      Click to browse or drag and drop roster file
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Supports CSV and Excel (.xlsx) files up to 2MB (max 500 students)
                    </p>
                  </div>
                )}
              </div>

              {/* Template Download & Format Guide */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Required Spreadsheet Columns
                    </h4>
                    <p className="text-xs text-slate-600 mt-0.5 font-mono">
                      prn, name, email, division
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => handleDownloadTemplate('csv')}
                      className="px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-100 flex items-center gap-1.5"
                    >
                      <Download className="w-3.5 h-3.5 text-slate-500" />
                      CSV Template
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDownloadTemplate('xlsx')}
                      className="px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-100 flex items-center gap-1.5"
                    >
                      <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                      Excel Template
                    </button>
                  </div>
                </div>
                <div className="text-xs text-slate-500 space-y-1">
                  <p>• <strong>prn:</strong> Institutional PRN (strings with leading zeros are preserved).</p>
                  <p>• <strong>email:</strong> Institutional email used by the student to authenticate.</p>
                  <p>• <strong>division:</strong> Class batch or division grouping (e.g. A, CS-1).</p>
                </div>
              </div>
            </div>
          )}

          {/* STAGE 2: PREVIEW & CONFLICT RESOLUTION */}
          {stage === 'preview' && previewData && (
            <div className="space-y-5">
              {/* Metric summary badges */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Total Rows</span>
                  <p className="text-xl font-bold text-slate-800 mt-0.5">{previewData.total_rows}</p>
                </div>
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-center">
                  <span className="text-xs font-semibold text-blue-600 uppercase">New Assignments</span>
                  <p className="text-xl font-bold text-blue-700 mt-0.5">
                    {previewData.new_assignments_count}
                  </p>
                </div>
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-center">
                  <span className="text-xs font-semibold text-emerald-600 uppercase">Matched Accounts</span>
                  <p className="text-xl font-bold text-emerald-700 mt-0.5">
                    {previewData.matched_count}
                  </p>
                </div>
                <div
                  className={`p-3 border rounded-lg text-center ${
                    previewData.conflicts_count > 0
                      ? 'bg-rose-50 border-rose-200'
                      : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <span
                    className={`text-xs font-semibold uppercase ${
                      previewData.conflicts_count > 0 ? 'text-rose-600' : 'text-slate-500'
                    }`}
                  >
                    Conflicts / Errors
                  </span>
                  <p
                    className={`text-xl font-bold mt-0.5 ${
                      previewData.conflicts_count > 0 ? 'text-rose-700' : 'text-slate-700'
                    }`}
                  >
                    {previewData.conflicts_count + previewData.errors.length}
                  </p>
                </div>
              </div>

              {/* Status Alert */}
              {previewData.can_confirm ? (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-xs text-emerald-800">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>
                    Validation passed. All {previewData.valid_rows} student record(s) are ready to be imported.
                  </span>
                </div>
              ) : (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2 text-xs text-rose-800">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Unresolved Conflicts Detected:</span> Import is blocked
                    until spreadsheet errors and student identity conflicts are corrected in your file.
                  </div>
                </div>
              )}

              {/* Syntax Errors list if any */}
              {previewData.errors.length > 0 && (
                <div className="border border-rose-200 bg-rose-50/50 rounded-lg p-3">
                  <h4 className="text-xs font-bold text-rose-800 uppercase tracking-wider mb-2">
                    Spreadsheet Errors
                  </h4>
                  <ul className="text-xs text-rose-700 space-y-1">
                    {previewData.errors.map((e, idx) => (
                      <li key={idx}>
                        • Row {e.row_number} {e.column ? `[${e.column}]` : ''}: {e.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Candidate Items Table */}
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-600 font-semibold sticky top-0 border-b border-slate-200">
                      <tr>
                        <th className="px-3 py-2">Row</th>
                        <th className="px-3 py-2">PRN</th>
                        <th className="px-3 py-2">Name</th>
                        <th className="px-3 py-2">Email</th>
                        <th className="px-3 py-2">Division</th>
                        <th className="px-3 py-2">Roster Status</th>
                        <th className="px-3 py-2">Account Match</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {previewData.items.map((it) => (
                        <tr
                          key={it.row_number}
                          className={it.conflict_reason ? 'bg-rose-50/60' : 'hover:bg-slate-50'}
                        >
                          <td className="px-3 py-2 font-mono text-slate-500">{it.row_number}</td>
                          <td className="px-3 py-2 font-mono font-medium text-slate-800">{it.prn}</td>
                          <td className="px-3 py-2 text-slate-700">{it.name}</td>
                          <td className="px-3 py-2 text-slate-600">{it.email}</td>
                          <td className="px-3 py-2">
                            <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-semibold text-[10px]">
                              {it.division}
                            </span>
                          </td>
                          <td className="px-3 py-2">
                            {it.assignment_status === 'new' && (
                              <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium text-[11px]">
                                New
                              </span>
                            )}
                            {it.assignment_status === 'already_assigned' && (
                              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[11px]">
                                Already Assigned
                              </span>
                            )}
                            {it.assignment_status === 'conflict' && (
                              <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-medium text-[11px]">
                                Conflict
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-2">
                            {it.match_status === 'matched' && (
                              <span className="inline-flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
                                <CheckCircle2 className="w-3.5 h-3.5" /> Matched
                              </span>
                            )}
                            {it.match_status === 'unregistered' && (
                              <span className="text-slate-500 text-[11px]">Pending Register</span>
                            )}
                            {it.match_status === 'pending_profile' && (
                              <span className="text-amber-700 text-[11px]">Profile Incomplete</span>
                            )}
                            {it.match_status === 'conflict' && (
                              <span
                                className="text-rose-600 font-medium text-[11px] cursor-help"
                                title={it.conflict_reason || ''}
                              >
                                {it.conflict_reason}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* STAGE 3: SUCCESS */}
          {stage === 'success' && importSummary && (
            <div className="py-8 text-center space-y-4">
              <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-slate-800">Roster Successfully Committed</h4>
                <p className="text-sm text-slate-600 mt-1 max-w-md mx-auto">
                  {importSummary.message}
                </p>
              </div>
              <div className="flex justify-center gap-6 pt-2 text-xs text-slate-500">
                <span>• {importSummary.imported_count} new assignments</span>
                <span>• {importSummary.already_assigned_count} updated</span>
                <span>• {importSummary.matched_accounts_count} accounts matched</span>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50">
          {stage === 'preview' ? (
            <button
              type="button"
              onClick={() => setStage('upload')}
              disabled={isProcessing}
              className="px-3.5 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 flex items-center gap-1.5 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Change File
            </button>
          ) : (
            <div />
          )}

          <div className="flex gap-3">
            {stage === 'upload' && (
              <>
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isProcessing}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handlePreview}
                  disabled={!selectedFile || isProcessing}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  {isProcessing ? 'Analyzing...' : 'Preview Roster'}
                </button>
              </>
            )}

            {stage === 'preview' && (
              <>
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isProcessing}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmImport}
                  disabled={!previewData?.can_confirm || isProcessing}
                  className="px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  {isProcessing ? 'Importing...' : 'Confirm & Commit Assignments'}
                </button>
              </>
            )}

            {stage === 'success' && (
              <button
                type="button"
                onClick={handleClose}
                className="px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Done
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}
