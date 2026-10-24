import React, { useState, useEffect, useCallback } from 'react'
import {
  Users,
  UserPlus,
  Upload,
  Download,
  Search,
  CheckCircle2,
  AlertCircle,
  Trash2,
  ShieldAlert,
  ShieldCheck,
  FileSpreadsheet,
  RefreshCw,
} from 'lucide-react'
import {
  fetchAssignments,
  updateAssignmentStatus,
  deleteAssignment,
  downloadRosterTemplate,
} from '../../services/rosterApi'
import type { Assignment, AssignmentSummaryStats } from '../../types/roster'
import { RosterImportModal } from './RosterImportModal'
import { AddStudentModal } from './AddStudentModal'

interface RosterTabProps {
  quizId: string
  token: string
}

export const RosterTab: React.FC<RosterTabProps> = ({ quizId, token }) => {
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [summary, setSummary] = useState<AssignmentSummaryStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [search, setSearch] = useState('')
  const [divisionFilter, setDivisionFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'revoked'>('all')

  // Modals
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const loadAssignments = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetchAssignments(token, quizId, {
        search: search.trim() || undefined,
        division: divisionFilter !== 'ALL' ? divisionFilter : undefined,
        is_active: statusFilter === 'all' ? undefined : statusFilter === 'active',
      })
      setAssignments(res.items)
      setSummary(res.summary)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load roster assignments.')
    } finally {
      setIsLoading(false)
    }
  }, [token, quizId, search, divisionFilter, statusFilter])

  useEffect(() => {
    loadAssignments()
  }, [loadAssignments])

  const handleStatusToggle = async (assignment: Assignment) => {
    try {
      const updated = await updateAssignmentStatus(token, quizId, assignment.id, !assignment.is_active)
      setAssignments((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
      // Refresh summary
      if (summary) {
        setSummary({
          ...summary,
          active_count: updated.is_active ? summary.active_count + 1 : summary.active_count - 1,
          revoked_count: !updated.is_active ? summary.revoked_count + 1 : summary.revoked_count - 1,
        })
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update assignment status.')
    }
  }

  const handleDelete = async (assignment: Assignment) => {
    if (assignment.has_attempts) {
      alert('Cannot delete student with historical attempts. Revoke their assignment instead.')
      return
    }

    if (!confirm(`Are you sure you want to remove ${assignment.student_name} (${assignment.student_prn}) from this quiz?`)) {
      return
    }

    setDeletingId(assignment.id)
    try {
      await deleteAssignment(token, quizId, assignment.id)
      setAssignments((prev) => prev.filter((a) => a.id !== assignment.id))
      loadAssignments()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete assignment.')
    } finally {
      setDeletingId(null)
    }
  }

  const handleDownloadTemplate = async (format: 'csv' | 'xlsx') => {
    try {
      await downloadRosterTemplate(token, quizId, format)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to download template.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Assigned
            </span>
            <p className="text-2xl font-bold text-slate-800 mt-1">{summary.total_assigned}</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">
              Active Eligible
            </span>
            <p className="text-2xl font-bold text-emerald-700 mt-1">{summary.active_count}</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider">
              Revoked Access
            </span>
            <p className="text-2xl font-bold text-rose-700 mt-1">{summary.revoked_count}</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider">
              Matched Accounts
            </span>
            <p className="text-2xl font-bold text-blue-700 mt-1">{summary.matched_count}</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Pending Signup
            </span>
            <p className="text-2xl font-bold text-slate-600 mt-1">{summary.unregistered_count}</p>
          </div>
        </div>
      )}

      {/* Action and Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row justify-between gap-3 items-stretch sm:items-center">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="px-3.5 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 shadow-sm"
            >
              <Upload className="w-4 h-4" />
              Upload Roster (CSV / Excel)
            </button>
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="px-3.5 py-2 text-sm font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-2"
            >
              <UserPlus className="w-4 h-4 text-blue-600" />
              Add Student
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadAssignments}
              disabled={isLoading}
              className="px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors flex items-center gap-1.5 shadow-2xs disabled:opacity-50"
              title="Refresh Roster List"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-600 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => handleDownloadTemplate('csv')}
              className="px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-800 bg-slate-50 border border-slate-200 rounded-md hover:bg-slate-100 transition-colors flex items-center gap-1.5"
              title="Download CSV sample template"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              CSV Template
            </button>
            <button
              onClick={() => handleDownloadTemplate('xlsx')}
              className="px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-800 bg-slate-50 border border-slate-200 rounded-md hover:bg-slate-100 transition-colors flex items-center gap-1.5"
              title="Download Excel sample template"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
              Excel Template
            </button>
          </div>
        </div>

        {/* Filter controls */}
        <div className="flex flex-col sm:flex-row gap-3 pt-3 border-t border-slate-100">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by PRN, name, or email..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={divisionFilter}
              onChange={(e) => setDivisionFilter(e.target.value)}
              className="px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700"
            >
              <option value="ALL">All Divisions</option>
              {summary?.divisions.map((d) => (
                <option key={d} value={d}>
                  Division {d}
                </option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'revoked')}
              className="px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700"
            >
              <option value="all">All Eligibility</option>
              <option value="active">Active Only</option>
              <option value="revoked">Revoked Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-sm text-rose-700">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Assignments Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-500">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
            <p className="text-sm">Loading assigned students...</p>
          </div>
        ) : assignments.length === 0 ? (
          <div className="py-16 text-center text-slate-500 space-y-3">
            <Users className="w-12 h-12 text-slate-300 mx-auto" />
            <p className="text-base font-semibold text-slate-700">No students assigned yet</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Upload a student roster spreadsheet or add students individually to grant test-taking access.
            </p>
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="mt-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Upload Student Roster
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 text-xs">
                <tr>
                  <th className="px-4 py-3">Student PRN</th>
                  <th className="px-4 py-3">Full Name</th>
                  <th className="px-4 py-3">Institutional Email</th>
                  <th className="px-4 py-3">Division</th>
                  <th className="px-4 py-3">Account Registration</th>
                  <th className="px-4 py-3">Access Eligibility</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {assignments.map((assignment) => (
                  <tr key={assignment.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-3 font-mono font-medium text-slate-800">
                      {assignment.student_prn}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900">{assignment.student_name}</td>
                    <td className="px-4 py-3 text-slate-600">{assignment.student_email}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-bold text-xs">
                        {assignment.division}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {assignment.assigned_student_id ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          Account Matched
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-medium border border-slate-200">
                          Pending Signup
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {assignment.is_active ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 text-xs font-semibold">
                          <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                          Revoked
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleStatusToggle(assignment)}
                          className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                            assignment.is_active
                              ? 'text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200'
                              : 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200'
                          }`}
                        >
                          {assignment.is_active ? 'Revoke' : 'Reactivate'}
                        </button>
                        <button
                          onClick={() => handleDelete(assignment)}
                          disabled={deletingId === assignment.id || assignment.has_attempts}
                          className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md hover:bg-slate-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                          title={
                            assignment.has_attempts
                              ? 'Cannot delete student with assessment attempts'
                              : 'Remove assignment'
                          }
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}
      <RosterImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        quizId={quizId}
        token={token}
        onImportSuccess={() => {
          loadAssignments()
        }}
      />

      <AddStudentModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        quizId={quizId}
        token={token}
        onStudentAdded={() => {
          loadAssignments()
        }}
      />
    </div>
  )
}
