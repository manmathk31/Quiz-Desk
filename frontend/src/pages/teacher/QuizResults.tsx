import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Download,
  Share2,
  Users,
  Award,
  AlertCircle,
  Clock,
  Search,
  CheckCircle2,
  RefreshCw,
  Eye,
  SlidersHorizontal,
  X,
  History,
  ShieldAlert,
  Shield,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import {
  fetchQuizResultSummary,
  fetchQuizAttempts,
  fetchAttemptDetail,
  adjustAttemptScore,
  releaseQuizResults,
  downloadQuizResultsCsv,
} from '../../services/resultsApi'
import type {
  QuizResultSummary,
  AttemptListItem,
  AttemptDetail,
} from '../../types/results'

export const QuizResults: React.FC = () => {
  const { quizId } = useParams<{ quizId: string }>()
  const navigate = useNavigate()
  const { session } = useAuth()
  const token = session?.access_token || ''

  // Summary State
  const [summary, setSummary] = useState<QuizResultSummary | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(true)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  // Attempts State
  const [attempts, setAttempts] = useState<AttemptListItem[]>([])
  const [totalAttempts, setTotalAttempts] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [attemptsLoading, setAttemptsLoading] = useState(true)
  const [attemptsError, setAttemptsError] = useState<string | null>(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  // Export State
  const [exporting, setExporting] = useState(false)
  const [exportSuccess, setExportSuccess] = useState(false)

  // Release Modal State
  const [showReleaseModal, setShowReleaseModal] = useState(false)
  const [releasing, setReleasing] = useState(false)

  // Detail & Adjustment Modal State
  const [selectedAttemptId, setSelectedAttemptId] = useState<string | null>(null)
  const [attemptDetail, setAttemptDetail] = useState<AttemptDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'questions' | 'telemetry' | 'adjustments'>('questions')

  // Score Adjustment Form State
  const [newScore, setNewScore] = useState<string>('')
  const [adjustmentReason, setAdjustmentReason] = useState('')
  const [adjusting, setAdjusting] = useState(false)
  const [adjustmentError, setAdjustmentError] = useState<string | null>(null)
  const [adjustmentSuccess, setAdjustmentSuccess] = useState(false)

  // Load Summary
  const loadSummary = useCallback(async () => {
    if (!token || !quizId) return
    try {
      setSummaryLoading(true)
      setSummaryError(null)
      const data = await fetchQuizResultSummary(token, quizId)
      setSummary(data)
    } catch (err: unknown) {
      setSummaryError(err instanceof Error ? err.message : 'Failed to load assessment summary.')
    } finally {
      setSummaryLoading(false)
    }
  }, [token, quizId])

  // Load Attempts
  const loadAttempts = useCallback(async () => {
    if (!token || !quizId) return
    try {
      setAttemptsLoading(true)
      setAttemptsError(null)
      const data = await fetchQuizAttempts(token, quizId, page, 15, statusFilter, searchTerm)
      setAttempts(data.items)
      setTotalAttempts(data.total)
      setTotalPages(data.total_pages)
    } catch (err: unknown) {
      setAttemptsError(err instanceof Error ? err.message : 'Failed to load attempts.')
    } finally {
      setAttemptsLoading(false)
    }
  }, [token, quizId, page, statusFilter, searchTerm])

  useEffect(() => {
    loadSummary()
  }, [loadSummary])

  useEffect(() => {
    loadAttempts()
  }, [loadAttempts])

  // Open Attempt Detail Modal
  const handleOpenDetail = async (attemptId: string) => {
    if (!token || !quizId) return
    setSelectedAttemptId(attemptId)
    setActiveTab('questions')
    setAdjustmentError(null)
    setAdjustmentSuccess(false)
    setAdjustmentReason('')

    try {
      setDetailLoading(true)
      setDetailError(null)
      const detail = await fetchAttemptDetail(token, quizId, attemptId)
      setAttemptDetail(detail)
      setNewScore(detail.total_score !== null ? detail.total_score.toString() : '0')
    } catch (err: unknown) {
      setDetailError(err instanceof Error ? err.message : 'Failed to load attempt details.')
    } finally {
      setDetailLoading(false)
    }
  }

  // Handle Score Adjustment
  const handleScoreAdjustment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !quizId || !selectedAttemptId) return

    const parsedScore = parseFloat(newScore)
    if (isNaN(parsedScore) || parsedScore < 0) {
      setAdjustmentError('Please enter a valid, non-negative score.')
      return
    }

    if (summary && parsedScore > summary.total_possible_marks) {
      setAdjustmentError(`Score cannot exceed maximum possible marks (${summary.total_possible_marks}).`)
      return
    }

    if (!adjustmentReason.trim() || adjustmentReason.trim().length < 3) {
      setAdjustmentError('Please provide a meaningful reason for the audit trail (min 3 characters).')
      return
    }

    try {
      setAdjusting(true)
      setAdjustmentError(null)
      const updated = await adjustAttemptScore(token, quizId, selectedAttemptId, {
        new_score: parsedScore,
        reason: adjustmentReason.trim(),
      })
      setAttemptDetail(updated)
      setAdjustmentSuccess(true)
      setAdjustmentReason('')
      // Refresh summary & attempts list in background
      loadSummary()
      loadAttempts()
    } catch (err: unknown) {
      setAdjustmentError(err instanceof Error ? err.message : 'Failed to adjust score.')
    } finally {
      setAdjusting(false)
    }
  }

  // Handle Result Release
  const handleReleaseResults = async () => {
    if (!token || !quizId) return
    try {
      setReleasing(true)
      await releaseQuizResults(token, quizId)
      setShowReleaseModal(false)
      await loadSummary()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to release results.')
    } finally {
      setReleasing(false)
    }
  }

  // Handle CSV Export
  const handleExportCsv = async () => {
    if (!token || !quizId) return
    try {
      setExporting(true)
      setExportSuccess(false)
      const blob = await downloadQuizResultsCsv(token, quizId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `quiz_${quizId}_results.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      setExportSuccess(true)
      setTimeout(() => setExportSuccess(false), 4000)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to export CSV.')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-slate-900">
      {/* Navigation & Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/teacher/quizzes')}
          className="inline-flex items-center text-xs font-medium text-slate-500 hover:text-slate-800 mb-3 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          Back to Assessments
        </button>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                {summary?.course_code || 'Assessment'}
              </span>
              <span className="text-xs font-medium text-slate-500">
                Version {summary?.version_number || 1}
              </span>
              {summary?.is_results_released ? (
                <span className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Results Released
                </span>
              ) : (
                <span className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                  <Clock className="w-3 h-3 mr-1" />
                  Results Withheld
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mt-1">
              {summary?.quiz_title || 'Assessment Results & Evaluation'}
            </h1>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleExportCsv}
              disabled={exporting}
              className="inline-flex items-center px-3.5 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5 mr-1.5" />
              {exporting ? 'Exporting...' : exportSuccess ? 'Downloaded!' : 'Export CSV'}
            </button>

            {!summary?.is_results_released && (
              <button
                onClick={() => setShowReleaseModal(true)}
                className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm"
              >
                <Share2 className="w-3.5 h-3.5 mr-1.5" />
                Release Results
              </button>
            )}
          </div>
        </div>
      </div>

      {/* KPI Summary Cards */}
      {summaryLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-24 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : summaryError ? (
        <div className="p-4 mb-6 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
          {summaryError}
        </div>
      ) : summary ? (
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Total Enrolled</span>
              <Users className="w-4 h-4 text-blue-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900">{summary.total_enrolled}</div>
            <p className="text-[11px] text-slate-500 mt-1">
              {summary.total_attempts} attempts initiated
            </p>
          </div>

          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Submitted & Graded</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900">{summary.submitted_count}</div>
            <p className="text-[11px] text-slate-500 mt-1">
              {summary.in_progress_count} currently in progress
            </p>
          </div>

          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Class Average</span>
              <Award className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {summary.average_score !== null ? summary.average_score.toFixed(2) : '—'}
              <span className="text-xs font-normal text-slate-400 ml-1">
                / {summary.total_possible_marks}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {summary.average_score !== null && summary.total_possible_marks > 0
                ? `${((summary.average_score / summary.total_possible_marks) * 100).toFixed(1)}% mean score`
                : 'Awaiting submissions'}
            </p>
          </div>

          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Score Range</span>
              <SlidersHorizontal className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {summary.highest_score !== null ? summary.highest_score.toFixed(1) : '—'}
              <span className="text-xs font-normal text-slate-400 mx-1">/</span>
              {summary.lowest_score !== null ? summary.lowest_score.toFixed(1) : '—'}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Highest / Lowest marks</p>
          </div>
        </div>
      ) : null}

      {/* Filter & Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6 shadow-xs">
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by PRN, Name, or Email..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setPage(1)
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-700"
            >
              <option value="all">All Statuses</option>
              <option value="submitted">Submitted</option>
              <option value="in_progress">In Progress</option>
              <option value="expired">Expired</option>
            </select>

            <button
              onClick={() => {
                loadSummary()
                loadAttempts()
              }}
              title="Refresh attempts list"
              className="p-1.5 text-slate-500 hover:text-slate-800 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Attempts Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        {attemptsLoading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />
            Loading assessment attempts...
          </div>
        ) : attemptsError ? (
          <div className="p-8 text-center text-xs text-red-600">
            <AlertCircle className="w-6 h-6 mx-auto mb-2 text-red-500" />
            {attemptsError}
          </div>
        ) : attempts.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            <Users className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="font-semibold text-slate-700 text-sm">No attempts found</p>
            <p className="text-slate-400 mt-1">
              {searchTerm || statusFilter !== 'all'
                ? 'Try adjusting your search criteria or status filter.'
                : 'Assigned students have not initiated any attempts yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3 px-4">Student</th>
                  <th className="py-3 px-4">PRN / Division</th>
                  <th className="py-3 px-4">Attempt</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Started / Submitted</th>
                  <th className="py-3 px-4">Score</th>
                  <th className="py-3 px-4">Grading</th>
                  <th className="py-3 px-4 text-center">Violations & Deduction</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {attempts.map((att) => (
                  <tr key={att.attempt_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-900">
                      <div>{att.student_name}</div>
                      <div className="text-[11px] text-slate-400 font-normal">{att.student_email}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-mono text-slate-800">{att.student_prn}</div>
                      <div className="text-[11px] text-slate-400">Div: {att.student_division}</div>
                    </td>
                    <td className="py-3 px-4 font-medium">#{att.attempt_number}</td>
                    <td className="py-3 px-4">
                      {att.status === 'submitted' && (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700">
                          Submitted
                        </span>
                      )}
                      {att.status === 'in_progress' && (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 animate-pulse">
                          In Progress
                        </span>
                      )}
                      {att.status === 'expired' && (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700">
                          Expired
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-500">
                      <div>
                        {att.started_at ? new Date(att.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                      </div>
                      <div className="text-slate-400">
                        {att.submitted_at ? new Date(att.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Ongoing'}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900">
                      {att.total_score !== null ? att.total_score.toFixed(2) : '—'}
                    </td>
                    <td className="py-3 px-4">
                      {att.grading_status === 'auto_graded' && (
                        <span className="text-[11px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                          Auto-Graded
                        </span>
                      )}
                      {att.grading_status === 'manually_adjusted' && (
                        <span className="text-[11px] text-indigo-700 bg-indigo-50 font-semibold px-2 py-0.5 rounded inline-flex items-center">
                          <History className="w-3 h-3 mr-1" />
                          Adjusted ({att.adjustment_count})
                        </span>
                      )}
                      {att.grading_status === 'pending' && (
                        <span className="text-[11px] text-slate-400">Pending</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="inline-flex flex-col items-center">
                        <span
                          className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                            (att.violation_count ?? att.tab_switch_count) > 2
                              ? 'bg-red-100 text-red-800'
                              : (att.violation_count ?? att.tab_switch_count) > 0
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {att.violation_count ?? att.tab_switch_count} violations
                        </span>
                        {Number(att.proctoring_deduction ?? 0) > 0 && (
                          <span className="text-[10px] text-red-600 font-bold mt-0.5">
                            -{Number(att.proctoring_deduction).toFixed(2)} pts
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenDetail(att.attempt_id)}
                        className="inline-flex items-center px-2.5 py-1 text-[11px] font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5 mr-1" />
                        Details & Grade
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
            <div>
              Showing page <span className="font-semibold">{page}</span> of{' '}
              <span className="font-semibold">{totalPages}</span> ({totalAttempts} total)
            </div>
            <div className="flex space-x-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 bg-white border border-slate-200 rounded disabled:opacity-40 hover:bg-slate-100 transition-colors"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-2.5 py-1 bg-white border border-slate-200 rounded disabled:opacity-40 hover:bg-slate-100 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Release Results Confirmation Modal */}
      {showReleaseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-xl text-slate-900 animate-in fade-in zoom-in-95 duration-150">
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mb-4">
              <Share2 className="w-6 h-6" />
            </div>

            <h3 className="text-lg font-bold text-slate-900">Release Assessment Results?</h3>
            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              Releasing results makes evaluated scores immediately visible to all assigned students
              in their student portals. Answer keys and other candidates&apos; marks remain protected.
            </p>

            <div className="my-4 p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1.5 text-slate-600">
              <div className="flex justify-between">
                <span>Assessment:</span>
                <span className="font-semibold text-slate-800">{summary?.quiz_title}</span>
              </div>
              <div className="flex justify-between">
                <span>Submitted attempts:</span>
                <span className="font-semibold text-slate-800">{summary?.submitted_count}</span>
              </div>
            </div>

            <div className="flex justify-end space-x-2.5 mt-6">
              <button
                onClick={() => setShowReleaseModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleReleaseResults}
                disabled={releasing}
                className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-50"
              >
                {releasing ? 'Releasing...' : 'Confirm & Release Results'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Attempt Detail & Manual Grade Adjustment Modal */}
      {selectedAttemptId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-150 text-slate-900 overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-slate-900">
                    {attemptDetail?.student_name || 'Attempt Details'}
                  </h3>
                  <span className="font-mono text-xs text-slate-500">
                    ({attemptDetail?.student_prn})
                  </span>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-800">
                    Attempt #{attemptDetail?.attempt_number}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Current Score:{' '}
                  <span className="font-bold text-slate-900">
                    {attemptDetail?.total_score !== null ? attemptDetail?.total_score : '—'}
                  </span>{' '}
                  / {attemptDetail?.max_possible_marks} marks &bull; Status:{' '}
                  <span className="capitalize">{attemptDetail?.status}</span>
                </p>
              </div>

              <button
                onClick={() => setSelectedAttemptId(null)}
                className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-200/50 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Tabs */}
            <div className="flex border-b border-slate-200 px-5 text-xs font-semibold text-slate-500 bg-white">
              <button
                onClick={() => setActiveTab('questions')}
                className={`py-3 mr-6 border-b-2 transition-colors ${
                  activeTab === 'questions'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent hover:text-slate-800'
                }`}
              >
                Question Responses ({attemptDetail?.questions.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('telemetry')}
                className={`py-3 mr-6 border-b-2 transition-colors ${
                  activeTab === 'telemetry'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent hover:text-slate-800'
                }`}
              >
                Telemetry & Proctoring ({attemptDetail?.telemetry_events.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('adjustments')}
                className={`py-3 border-b-2 transition-colors ${
                  activeTab === 'adjustments'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent hover:text-slate-800'
                }`}
              >
                Adjustment Audit ({attemptDetail?.adjustments.length || 0})
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto flex-1 space-y-4">
              {detailLoading ? (
                <div className="py-12 text-center text-xs text-slate-500">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />
                  Loading attempt diagnostics...
                </div>
              ) : detailError ? (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                  {detailError}
                </div>
              ) : attemptDetail ? (
                <>
                  {/* Tab 1: Questions & Answers */}
                  {activeTab === 'questions' && (
                    <div className="space-y-4">
                      {attemptDetail.questions.map((q, idx) => (
                        <div
                          key={q.question_id}
                          className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-3"
                        >
                          <div className="flex items-start justify-between">
                            <span className="font-semibold text-slate-800">
                              Q{idx + 1}. {q.prompt}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded font-bold ${
                                (q.awarded_marks || 0) > 0
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : (q.awarded_marks || 0) < 0
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-slate-200 text-slate-700'
                              }`}
                            >
                              {q.awarded_marks !== null ? q.awarded_marks : '0'} / {q.positive_marks} marks
                            </span>
                          </div>

                          <div className="space-y-1.5 pl-2">
                            {q.options.map((opt) => {
                              const isSelected = q.selected_option_ids.includes(opt.id)
                              return (
                                <div
                                  key={opt.id}
                                  className={`p-2 rounded-lg border flex items-center justify-between ${
                                    opt.is_correct && isSelected
                                      ? 'bg-emerald-50 border-emerald-300 text-emerald-900 font-medium'
                                      : opt.is_correct
                                      ? 'bg-emerald-50/50 border-dashed border-emerald-300 text-emerald-800'
                                      : isSelected
                                      ? 'bg-red-50 border-red-300 text-red-900'
                                      : 'bg-white border-slate-200 text-slate-600'
                                  }`}
                                >
                                  <div className="flex items-center space-x-2">
                                    <span className="w-2 h-2 rounded-full bg-slate-400" />
                                    <span>{opt.option_text}</span>
                                  </div>
                                  <div className="flex items-center space-x-2 text-[10px] font-semibold">
                                    {opt.is_correct && (
                                      <span className="text-emerald-700 uppercase">Correct Answer</span>
                                    )}
                                    {isSelected && (
                                      <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                                        Selected
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 2: Proctoring Telemetry */}
                  {activeTab === 'telemetry' && (
                    <div className="space-y-4">
                      {/* Proctoring Policy & Summary Card */}
                      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                          <div className="flex items-center space-x-2">
                            <Shield className="w-4 h-4 text-blue-600" />
                            <span className="font-bold text-slate-800 text-xs">
                              Proctoring Summary & Policy Snapshot
                            </span>
                          </div>
                          <span className="text-[11px] font-mono text-slate-500">
                            Version {attemptDetail.effective_policy?.version_number ?? 1}
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-2 text-center text-xs">
                          <div className="p-2 bg-white border border-slate-200 rounded-lg">
                            <div className="text-base font-bold text-slate-900">
                              {attemptDetail.violation_count ?? attemptDetail.tab_switch_count}
                            </div>
                            <div className="text-[10px] text-slate-500 uppercase font-semibold">Accepted Violations</div>
                          </div>
                          <div className="p-2 bg-white border border-slate-200 rounded-lg">
                            <div className="text-base font-bold text-blue-600">
                              {attemptDetail.effective_policy?.free_allowance ?? 2}
                            </div>
                            <div className="text-[10px] text-slate-500 uppercase font-semibold">Free Allowance</div>
                          </div>
                          <div className="p-2 bg-white border border-slate-200 rounded-lg">
                            <div className="text-base font-bold text-red-600">
                              -{Number(attemptDetail.proctoring_deduction ?? 0).toFixed(2)}
                            </div>
                            <div className="text-[10px] text-slate-500 uppercase font-semibold">Deduction Applied</div>
                          </div>
                        </div>

                        {/* Breakdown Chips */}
                        {attemptDetail.violation_breakdown && Object.keys(attemptDetail.violation_breakdown).length > 0 && (
                          <div className="pt-2 border-t border-slate-200 flex flex-wrap gap-2 items-center">
                            <span className="text-[11px] font-semibold text-slate-600">Detected Breakdown:</span>
                            {Object.entries(attemptDetail.violation_breakdown).map(([type, count]) => (
                              <span
                                key={type}
                                className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-100 text-amber-800 border border-amber-200"
                              >
                                {type.replace(/_/g, ' ')}: {count}
                              </span>
                            ))}
                          </div>
                        )}

                        {attemptDetail.effective_policy && (
                          <div className="text-[11px] text-slate-500 leading-relaxed bg-white p-2.5 rounded border border-slate-200 space-y-1">
                            <div>
                              <strong>Penalty Formula:</strong> max(0, V - {attemptDetail.effective_policy.free_allowance}) × {Number(attemptDetail.effective_policy.deduction_per_violation).toFixed(2)} pts (capped at {Number(attemptDetail.effective_policy.max_deduction).toFixed(2)} pts)
                            </div>
                            <div className="text-[10px] text-slate-400">
                              Enforced: Fullscreen ({attemptDetail.effective_policy.require_fullscreen ? 'Yes' : 'No'}), Copy/Paste Restriction ({attemptDetail.effective_policy.enable_copy_paste_restriction ? 'Yes' : 'No'}), DevTools Intercept ({attemptDetail.effective_policy.count_dev_tools_violations ? 'Yes' : 'No'})
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Timestamped Telemetry Event Log */}
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                          Timestamped Event Log ({attemptDetail.telemetry_events.length})
                        </h4>
                        {attemptDetail.telemetry_events.length === 0 ? (
                          <div className="py-6 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-slate-200">
                            <CheckCircle2 className="w-5 h-5 mx-auto mb-1 text-emerald-500" />
                            Zero suspicious browser events recorded during this attempt.
                          </div>
                        ) : (
                          attemptDetail.telemetry_events.map((t) => (
                            <div
                              key={t.id}
                              className="p-3 bg-amber-50/60 border border-amber-200 rounded-xl text-xs flex items-center justify-between"
                            >
                              <div className="flex items-center space-x-2">
                                <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
                                <div>
                                  <span className="font-semibold text-slate-800 uppercase text-[11px] block">
                                    {t.event_type.replace(/_/g, ' ')}
                                  </span>
                                  {t.client_event_id && (
                                    <span className="text-[10px] text-slate-400 font-mono">
                                      ID: {t.client_event_id.slice(0, 16)}...
                                    </span>
                                  )}
                                </div>
                              </div>
                              <span className="text-slate-500 font-mono text-[11px]">
                                {new Date(t.event_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                              </span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Adjustments History */}
                  {activeTab === 'adjustments' && (
                    <div className="space-y-3">
                      {attemptDetail.adjustments.length === 0 ? (
                        <div className="py-8 text-center text-xs text-slate-400">
                          No manual score adjustments have been made.
                        </div>
                      ) : (
                        attemptDetail.adjustments.map((adj) => (
                          <div
                            key={adj.id}
                            className="p-3 bg-indigo-50/50 border border-indigo-200 rounded-xl text-xs space-y-1"
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span className="text-indigo-900">
                                {adj.previous_score} &rarr; {adj.new_score} marks
                              </span>
                              <span className="text-[11px] text-slate-400">
                                {new Date(adj.created_at).toLocaleString()}
                              </span>
                            </div>
                            <p className="text-slate-700 italic text-[11px]">
                              &ldquo;{adj.reason}&rdquo;
                            </p>
                            <p className="text-[10px] text-slate-500">
                              Adjusted by: {adj.adjusted_by_name}
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {/* Manual Adjustment Form */}
                  <div className="mt-6 pt-5 border-t border-slate-200 bg-slate-50 -mx-5 -mb-5 p-5">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                      Manual Score Adjustment
                    </h4>

                    {adjustmentSuccess && (
                      <div className="mb-3 p-2 bg-emerald-100 text-emerald-800 rounded-lg text-xs font-semibold">
                        Score successfully updated and recorded in the audit trail.
                      </div>
                    )}

                    {adjustmentError && (
                      <div className="mb-3 p-2 bg-red-100 text-red-800 rounded-lg text-xs font-semibold">
                        {adjustmentError}
                      </div>
                    )}

                    <form onSubmit={handleScoreAdjustment} className="space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                        <div className="sm:col-span-1">
                          <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                            New Total Score
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            min="0"
                            max={attemptDetail.max_possible_marks}
                            value={newScore}
                            onChange={(e) => setNewScore(e.target.value)}
                            className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 font-semibold"
                            required
                          />
                        </div>
                        <div className="sm:col-span-3">
                          <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                            Justification / Reason (Mandatory Audit Trail)
                          </label>
                          <input
                            type="text"
                            placeholder="e.g., Partial credit for step 2 algorithm derivation"
                            value={adjustmentReason}
                            onChange={(e) => setAdjustmentReason(e.target.value)}
                            className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                            required
                          />
                        </div>
                      </div>

                      <div className="flex justify-end pt-1">
                        <button
                          type="submit"
                          disabled={adjusting || attemptDetail.status === 'in_progress'}
                          className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors shadow-xs disabled:opacity-50"
                        >
                          {adjusting ? 'Saving Adjustment...' : 'Apply Score Adjustment'}
                        </button>
                      </div>
                    </form>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
