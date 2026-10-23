import React, { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'
import {
  fetchAdminOverview,
  fetchAdminUsers,
  updateAdminUserStatus,
  fetchAdminAuditLogs,
  fetchResetStatus,
  executeDestructiveReset,
} from '../../services/adminApi'
import type {
  AdminOverviewResponse,
  AdminUserListItem,
  AdminAuditLogItem,
  AdminResetStatusResponse,
  AdminDestructiveResetResponse,
} from '../../types/admin'
import {
  Shield,
  Users,
  GraduationCap,
  BookOpen,
  FileText,
  Activity,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Trash2,
  Lock,
  ChevronLeft,
  ChevronRight,
  Database,
  Info,
} from 'lucide-react'

type DashboardTab = 'overview' | 'users' | 'audit' | 'reset'

export const AdminDashboard: React.FC = () => {
  const { session, user: authUser } = useAuth()
  const token = session?.access_token || ''

  const [activeTab, setActiveTab] = useState<DashboardTab>('overview')
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Overview state
  const [overviewData, setOverviewData] = useState<AdminOverviewResponse | null>(null)

  // User directory state
  const [users, setUsers] = useState<AdminUserListItem[]>([])
  const [totalUsers, setTotalUsers] = useState(0)
  const [userPage, setUserPage] = useState(1)
  const [userSearch, setUserSearch] = useState('')
  const [userRoleFilter, setUserRoleFilter] = useState('all')
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null)

  // Audit logs state
  const [auditLogs, setAuditLogs] = useState<AdminAuditLogItem[]>([])
  const [totalLogs, setTotalLogs] = useState(0)
  const [logPage, setLogPage] = useState(1)
  const [logActionFilter, setLogActionFilter] = useState('')

  // Reset state
  const [resetStatus, setResetStatus] = useState<AdminResetStatusResponse | null>(null)
  const [showResetModal, setShowResetModal] = useState(false)
  const [resetConfirmInput, setResetConfirmInput] = useState('')
  const [resetting, setResetting] = useState(false)
  const [resetResult, setResetResult] = useState<AdminDestructiveResetResponse | null>(null)

  // 1. Load Overview Data
  const loadOverview = useCallback(async () => {
    if (!token) return
    try {
      setLoading(true)
      const data = await fetchAdminOverview(token)
      setOverviewData(data)
      setErrorMsg(null)
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to load admin overview metrics.')
    } finally {
      setLoading(false)
    }
  }, [token])

  // 2. Load User Directory
  const loadUsers = useCallback(async () => {
    if (!token) return
    try {
      setLoading(true)
      const data = await fetchAdminUsers(token, userPage, 15, userSearch, userRoleFilter)
      setUsers(data.items)
      setTotalUsers(data.total)
      setErrorMsg(null)
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to load user directory.')
    } finally {
      setLoading(false)
    }
  }, [token, userPage, userSearch, userRoleFilter])

  // 3. Load Audit Logs
  const loadAuditLogs = useCallback(async () => {
    if (!token) return
    try {
      setLoading(true)
      const data = await fetchAdminAuditLogs(token, logPage, 20, logActionFilter)
      setAuditLogs(data.items)
      setTotalLogs(data.total)
      setErrorMsg(null)
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to load audit trail.')
    } finally {
      setLoading(false)
    }
  }, [token, logPage, logActionFilter])

  // 4. Load Reset Status
  const loadResetStatus = useCallback(async () => {
    if (!token) return
    try {
      setLoading(true)
      const data = await fetchResetStatus(token)
      setResetStatus(data)
      setErrorMsg(null)
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to check reset status.')
    } finally {
      setLoading(false)
    }
  }, [token])

  // Trigger loads based on active tab
  useEffect(() => {
    if (activeTab === 'overview') {
      loadOverview()
    } else if (activeTab === 'users') {
      loadUsers()
    } else if (activeTab === 'audit') {
      loadAuditLogs()
    } else if (activeTab === 'reset') {
      loadResetStatus()
    }
  }, [activeTab, loadOverview, loadUsers, loadAuditLogs, loadResetStatus])

  // User status toggle
  const handleToggleUserStatus = async (user: AdminUserListItem) => {
    if (user.email === authUser?.email) {
      setErrorMsg('Administrators cannot deactivate their own account.')
      return
    }

    const nextStatus = !user.is_active
    const confirmPrompt = `Are you sure you want to ${
      nextStatus ? 'activate' : 'deactivate'
    } account for ${user.name} (${user.email})?`
    if (!window.confirm(confirmPrompt)) return

    try {
      setUpdatingUserId(user.id)
      setErrorMsg(null)
      const updated = await updateAdminUserStatus(token, user.id, nextStatus)
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? { ...u, is_active: updated.is_active } : u)))
      setSuccessMsg(`User ${user.email} is now ${nextStatus ? 'active' : 'inactive'}.`)
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to update user status.')
    } finally {
      setUpdatingUserId(null)
    }
  }

  // Guarded Reset Execution
  const handleExecuteReset = async (e: React.FormEvent) => {
    e.preventDefault()
    if (resetConfirmInput !== 'CONFIRM_DELETE_ALL_TEST_DATA') {
      setErrorMsg("Confirmation code must be strictly 'CONFIRM_DELETE_ALL_TEST_DATA'.")
      return
    }

    try {
      setResetting(true)
      setErrorMsg(null)
      const res = await executeDestructiveReset(token, resetConfirmInput)
      setResetResult(res)
      setShowResetModal(false)
      setResetConfirmInput('')
      setSuccessMsg('All test data was permanently cleared. System restored to empty state.')
      loadResetStatus()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Destructive reset failed.')
    } finally {
      setResetting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 bg-amber-500/20 border border-amber-500/40 rounded-xl flex items-center justify-center text-amber-400">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight">System Admin Portal</h1>
              <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                Restricted
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Authoritative platform operations, user directory, audit trails, and maintenance
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400">Signed in as:</span>
          <span className="font-mono text-slate-200 font-medium">{authUser?.email}</span>
        </div>
      </div>

      {/* Global Alerts */}
      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMsg(null)}
            className="text-rose-500 hover:text-rose-800 font-bold ml-2"
          >
            ×
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-start justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button
            type="button"
            onClick={() => setSuccessMsg(null)}
            className="text-emerald-500 hover:text-emerald-800 font-bold ml-2"
          >
            ×
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-sm font-medium">
        <button
          type="button"
          onClick={() => setActiveTab('overview')}
          className={`pb-3 px-1 border-b-2 transition-colors flex items-center space-x-2 ${
            activeTab === 'overview'
              ? 'border-amber-600 text-amber-700 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Overview & Metrics</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('users')}
          className={`pb-3 px-1 border-b-2 transition-colors flex items-center space-x-2 ${
            activeTab === 'users'
              ? 'border-amber-600 text-amber-700 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>User Directory</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('audit')}
          className={`pb-3 px-1 border-b-2 transition-colors flex items-center space-x-2 ${
            activeTab === 'audit'
              ? 'border-amber-600 text-amber-700 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Audit Log Trail</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('reset')}
          className={`pb-3 px-1 border-b-2 transition-colors flex items-center space-x-2 ${
            activeTab === 'reset'
              ? 'border-rose-600 text-rose-700 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Trash2 className="w-4 h-4 text-rose-500" />
          <span>Guarded Reset</span>
        </button>
      </div>

      {/* TAB 1: OVERVIEW & METRICS */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {overviewData && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-medium">Students</span>
                  <GraduationCap className="w-4 h-4 text-blue-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900 font-mono">
                  {overviewData.stats.total_students}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Registered candidates</p>
              </div>

              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-medium">Teachers</span>
                  <BookOpen className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900 font-mono">
                  {overviewData.stats.total_teachers}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Faculty educators</p>
              </div>

              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-medium">Total Quizzes</span>
                  <FileText className="w-4 h-4 text-slate-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900 font-mono">
                  {overviewData.stats.total_quizzes}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Draft & published</p>
              </div>

              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-medium">Published</span>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900 font-mono">
                  {overviewData.stats.published_quizzes}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Active assessments</p>
              </div>

              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-medium">In Progress</span>
                  <Activity className="w-4 h-4 text-amber-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900 font-mono">
                  {overviewData.stats.active_attempts}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Live active attempts</p>
              </div>

              <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-medium">Total Attempts</span>
                  <Database className="w-4 h-4 text-purple-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900 font-mono">
                  {overviewData.stats.total_attempts}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Lifetime candidate submissions</p>
              </div>
            </div>
          )}

          {/* Recent System Activity */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-900">Recent Platform Activity</h2>
              <button
                type="button"
                onClick={loadOverview}
                disabled={loading}
                className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>

            {overviewData?.recent_activity.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No recent activity events recorded yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-50 text-slate-600">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium">Timestamp</th>
                      <th className="px-4 py-3 text-left font-medium">Action</th>
                      <th className="px-4 py-3 text-left font-medium">Entity Type</th>
                      <th className="px-4 py-3 text-left font-medium">Entity ID</th>
                      <th className="px-4 py-3 text-left font-medium">User Email</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {overviewData?.recent_activity.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-2.5 whitespace-nowrap text-slate-500 font-mono text-[11px]">
                          {new Date(item.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-2.5 font-medium text-slate-900">
                          <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-[11px]">
                            {item.action}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-slate-600 capitalize">{item.entity_type}</td>
                        <td className="px-4 py-2.5 font-mono text-[11px] text-slate-500 max-w-[120px] truncate">
                          {item.entity_id}
                        </td>
                        <td className="px-4 py-2.5 text-slate-600 font-mono text-[11px]">
                          {item.user_email || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: USER DIRECTORY */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center space-x-2 flex-1 max-w-md">
              <div className="relative w-full">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search by name, email, or PRN..."
                  value={userSearch}
                  onChange={(e) => {
                    setUserSearch(e.target.value)
                    setUserPage(1)
                  }}
                  className="w-full pl-9 pr-3 py-1.5 border border-slate-300 rounded-lg text-xs placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <select
                value={userRoleFilter}
                onChange={(e) => {
                  setUserRoleFilter(e.target.value)
                  setUserPage(1)
                }}
                className="px-2.5 py-1.5 border border-slate-300 rounded-lg text-xs bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="all">All Roles</option>
                <option value="student">Students</option>
                <option value="teacher">Teachers</option>
                <option value="admin">Administrators</option>
              </select>

              <button
                type="button"
                onClick={loadUsers}
                disabled={loading}
                className="p-1.5 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-100"
                title="Refresh user directory"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">User Name</th>
                    <th className="px-4 py-3 text-left font-medium">Email</th>
                    <th className="px-4 py-3 text-left font-medium">Role</th>
                    <th className="px-4 py-3 text-left font-medium">PRN / Division</th>
                    <th className="px-4 py-3 text-left font-medium">Status</th>
                    <th className="px-4 py-3 text-left font-medium">Created At</th>
                    <th className="px-4 py-3 text-right font-medium">Operational Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                        No users matching query.
                      </td>
                    </tr>
                  ) : (
                    users.map((u) => {
                      const isSelf = u.email === authUser?.email
                      return (
                        <tr key={u.id} className="hover:bg-slate-50/60">
                          <td className="px-4 py-3 font-semibold text-slate-900">{u.name}</td>
                          <td className="px-4 py-3 font-mono text-[11px] text-slate-600">{u.email}</td>
                          <td className="px-4 py-3">
                            <span
                              className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded ${
                                u.role === 'admin'
                                  ? 'bg-amber-100 text-amber-800'
                                  : u.role === 'teacher'
                                  ? 'bg-indigo-100 text-indigo-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {u.role}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px]">
                            {u.prn ? (
                              <span>
                                {u.prn} {u.division && <span className="text-slate-400">({u.division})</span>}
                              </span>
                            ) : (
                              <span className="text-slate-400">—</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {u.is_active ? (
                              <span className="inline-flex items-center space-x-1 text-emerald-700 font-medium">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                <span>Active</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center space-x-1 text-rose-700 font-medium">
                                <XCircle className="w-3.5 h-3.5 text-rose-600" />
                                <span>Deactivated</span>
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                            {new Date(u.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {isSelf ? (
                              <span className="px-2 py-1 bg-slate-100 text-slate-500 text-[10px] font-medium rounded">
                                Current Admin
                              </span>
                            ) : (
                              <button
                                type="button"
                                disabled={updatingUserId === u.id}
                                onClick={() => handleToggleUserStatus(u)}
                                className={`px-2.5 py-1 text-[11px] font-medium rounded transition-colors ${
                                  u.is_active
                                    ? 'text-rose-600 hover:bg-rose-50 border border-rose-200'
                                    : 'text-emerald-700 hover:bg-emerald-50 border border-emerald-300'
                                }`}
                              >
                                {updatingUserId === u.id
                                  ? 'Updating...'
                                  : u.is_active
                                  ? 'Deactivate'
                                  : 'Activate'}
                              </button>
                            )}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span>
                Showing {users.length} of {totalUsers} total users
              </span>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  disabled={userPage <= 1}
                  onClick={() => setUserPage((p) => p - 1)}
                  className="p-1 rounded border border-slate-200 disabled:opacity-40 hover:bg-white"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="font-mono">Page {userPage}</span>
                <button
                  type="button"
                  disabled={userPage * 15 >= totalUsers}
                  onClick={() => setUserPage((p) => p + 1)}
                  className="p-1 rounded border border-slate-200 disabled:opacity-40 hover:bg-white"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                placeholder="Filter by action (e.g. system.destructive_reset)..."
                value={logActionFilter}
                onChange={(e) => {
                  setLogActionFilter(e.target.value)
                  setLogPage(1)
                }}
                className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs w-72 focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
              <button
                type="button"
                onClick={loadAuditLogs}
                disabled={loading}
                className="p-1.5 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-100"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Timestamp</th>
                    <th className="px-4 py-3 text-left font-medium">Action</th>
                    <th className="px-4 py-3 text-left font-medium">Entity</th>
                    <th className="px-4 py-3 text-left font-medium">Actor Email</th>
                    <th className="px-4 py-3 text-left font-medium">Event Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                        No audit events match current criteria.
                      </td>
                    </tr>
                  ) : (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-2.5 whitespace-nowrap text-slate-500 font-mono text-[11px]">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-2.5 font-medium">
                          <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-[11px] text-slate-900">
                            {log.action}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 font-mono text-[11px] text-slate-600">
                          {log.entity_type}:{log.entity_id}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-[11px] text-slate-600">
                          {log.user_email || 'System / Anonymous'}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-[10px] text-slate-500 max-w-xs truncate">
                          {log.details ? JSON.stringify(log.details) : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span>
                Showing {auditLogs.length} of {totalLogs} total audit logs
              </span>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  disabled={logPage <= 1}
                  onClick={() => setLogPage((p) => p - 1)}
                  className="p-1 rounded border border-slate-200 disabled:opacity-40 hover:bg-white"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="font-mono">Page {logPage}</span>
                <button
                  type="button"
                  disabled={logPage * 20 >= totalLogs}
                  onClick={() => setLogPage((p) => p + 1)}
                  className="p-1 rounded border border-slate-200 disabled:opacity-40 hover:bg-white"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: GUARDED TEST DATA RESET */}
      {activeTab === 'reset' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 rounded-xl bg-rose-100 flex items-center justify-center text-rose-600 flex-shrink-0">
                <Trash2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h2 className="text-base font-bold text-slate-900">Guarded Database / Test Data Reset</h2>
                <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
                  High-risk maintenance utility intended solely for developer testing and QA rehearsal.
                  Clears application assessment data (quizzes, immutable versions, question banks, roster
                  assignments, candidate attempts, answers, and telemetry) to return the environment to an
                  empty baseline.
                </p>
              </div>
            </div>

            {/* Safeguard Status Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                <span className="text-slate-500 font-medium">Server Environment</span>
                <div className="font-mono font-semibold text-slate-800 uppercase">
                  {resetStatus?.environment || 'Unknown'}
                </div>
              </div>

              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                <span className="text-slate-500 font-medium">Reset Feature Flag</span>
                <div className="flex items-center space-x-1.5 font-semibold">
                  {resetStatus?.allow_destructive_reset ? (
                    <span className="text-emerald-700 font-mono">ALLOW_DESTRUCTIVE_RESET=true</span>
                  ) : (
                    <span className="text-rose-700 font-mono">ALLOW_DESTRUCTIVE_RESET=false</span>
                  )}
                </div>
              </div>

              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                <span className="text-slate-500 font-medium">Execution Eligibility</span>
                <div className="flex items-center space-x-1.5 font-semibold">
                  {resetStatus?.can_reset ? (
                    <span className="text-amber-700">Permitted in Non-Production</span>
                  ) : (
                    <span className="text-rose-700 flex items-center space-x-1">
                      <Lock className="w-3.5 h-3.5" />
                      <span>Blocked & Disabled</span>
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Notice & Safeguard Breakdown */}
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-xs space-y-2 text-amber-900">
              <div className="flex items-center space-x-2 font-semibold">
                <Info className="w-4 h-4 text-amber-600" />
                <span>Safeguards & Preservation Policy</span>
              </div>
              <ul className="list-disc pl-5 space-y-1 text-slate-700">
                <li>
                  <strong>Accounts Preserved:</strong> User authentication accounts (Administrators,
                  Teachers, and Students) are strictly preserved so you never lose administrative access.
                </li>
                <li>
                  <strong>Audit History Preserved:</strong> The tamper-evident audit log is kept intact, and
                  a distinct <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">system.destructive_reset</code> event is recorded with details.
                </li>
                <li>
                  <strong>Production Hard Block:</strong> When <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">ENVIRONMENT=production</code>, this endpoint unconditionally returns 403 Forbidden.
                </li>
                <li>
                  <strong>Explicit Confirmation:</strong> Requires submitting token <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">CONFIRM_DELETE_ALL_TEST_DATA</code>.
                </li>
              </ul>
            </div>

            {/* Action Trigger */}
            <div className="pt-2">
              {resetStatus?.can_reset ? (
                <button
                  type="button"
                  onClick={() => setShowResetModal(true)}
                  className="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Initiate Guarded Test Data Reset</span>
                </button>
              ) : (
                <div className="p-3 bg-slate-100 border border-slate-200 rounded-lg text-xs text-slate-600 flex items-center space-x-2">
                  <Lock className="w-4 h-4 text-slate-500" />
                  <span>
                    Destructive reset is currently disabled by system configuration. To enable for local testing,
                    set <code className="font-mono bg-slate-200 px-1 rounded">ALLOW_DESTRUCTIVE_RESET=true</code> in backend environment.
                  </span>
                </div>
              )}
            </div>

            {/* Last Execution Outcome */}
            {resetResult && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                <span className="font-semibold text-slate-900">Last Reset Results:</span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px] text-slate-700">
                  {Object.entries(resetResult.cleared_records).map(([table, count]) => (
                    <div key={table} className="p-2 bg-white rounded border border-slate-200">
                      <div className="text-slate-500 text-[10px]">{table}</div>
                      <div className="font-bold text-slate-900">{count} removed</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: GUARDED RESET CONFIRMATION */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center space-x-3 text-rose-600">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <h3 className="text-base font-bold text-slate-900">Confirm Destructive Reset</h3>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              This action will permanently delete all quizzes, immutable versions, question banks,
              roster assignments, and candidate attempts. Administrator access will remain intact,
              and this operation will be permanently recorded in the audit log.
            </p>

            <form onSubmit={handleExecuteReset} className="space-y-4 pt-2">
              <div>
                <label htmlFor="confirm-code" className="block text-xs font-semibold text-slate-700 mb-1">
                  Type <span className="font-mono text-rose-600 bg-rose-50 px-1 py-0.5 rounded">CONFIRM_DELETE_ALL_TEST_DATA</span> to verify:
                </label>
                <input
                  id="confirm-code"
                  type="text"
                  required
                  value={resetConfirmInput}
                  onChange={(e) => setResetConfirmInput(e.target.value)}
                  placeholder="CONFIRM_DELETE_ALL_TEST_DATA"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-rose-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  disabled={resetting}
                  onClick={() => {
                    setShowResetModal(false)
                    setResetConfirmInput('')
                  }}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resetting || resetConfirmInput !== 'CONFIRM_DELETE_ALL_TEST_DATA'}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>{resetting ? 'Executing Reset...' : 'Permanently Delete Test Data'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
