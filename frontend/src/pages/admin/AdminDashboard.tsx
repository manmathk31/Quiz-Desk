import React, { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'
import {
  fetchAdminOverview,
  fetchAdminUsers,
  updateAdminUserStatus,
  fetchAdminAuditLogs,
  fetchResetStatus,
  executeDestructiveReset,
  createAdminTeacher,
  purgeAdminUser,
  executeCleanTeacherWorkspace,
} from '../../services/adminApi'
import type {
  AdminOverviewResponse,
  AdminUserListItem,
  AdminAuditLogItem,
  AdminResetStatusResponse,
  AdminDestructiveResetResponse,
  AdminUserPurgeResponse,
  AdminCleanWorkspaceResponse,
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
  UserPlus,
  UserX,
  Eye,
  EyeOff,
  Copy,
  Check,

  Sparkles,
  AlertOctagon,
  RotateCcw,
} from 'lucide-react'

type DashboardTab = 'overview' | 'users' | 'purge' | 'audit' | 'reset'


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

  // Faculty Onboarding Modal state
  const [showTeacherModal, setShowTeacherModal] = useState(false)
  const [teacherName, setTeacherName] = useState('')
  const [teacherEmail, setTeacherEmail] = useState('')
  const [teacherPassword, setTeacherPassword] = useState('')
  const [showTeacherPass, setShowTeacherPass] = useState(false)
  const [creatingTeacher, setCreatingTeacher] = useState(false)
  const [createdTeacherCreds, setCreatedTeacherCreds] = useState<{
    name: string
    email: string
    password: string
  } | null>(null)
  const [credsCopied, setCredsCopied] = useState(false)

  // Cautious User Purge state
  const [purgeTargetEmail, setPurgeTargetEmail] = useState('')
  const [purgeAdminPassword, setPurgeAdminPassword] = useState('')
  const [purgeConfirmEmail, setPurgeConfirmEmail] = useState('')
  const [showPurgePass, setShowPurgePass] = useState(false)
  const [purgingUser, setPurgingUser] = useState(false)
  const [purgeResult, setPurgeResult] = useState<AdminUserPurgeResponse | null>(null)

  // Clean Teacher Workspace state
  const [showCleanWorkspaceModal, setShowCleanWorkspaceModal] = useState(false)
  const [cleanWorkspaceConfirmInput, setCleanWorkspaceConfirmInput] = useState('')
  const [cleaningWorkspace, setCleaningWorkspace] = useState(false)
  const [cleanWorkspaceResult, setCleanWorkspaceResult] = useState<AdminCleanWorkspaceResponse | null>(null)

  // Helper: Generate Secure Password
  const generateRandomPassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%^&*'
    let pwd = 'Quiz@'
    for (let i = 0; i < 8; i++) {
      pwd += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    setTeacherPassword(pwd)
  }


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

  // Handle Faculty Onboarding
  const handleCreateTeacher = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!teacherEmail.trim() || !teacherName.trim() || !teacherPassword.trim()) {
      setErrorMsg('All fields are required to onboard a faculty member.')
      return
    }

    try {
      setCreatingTeacher(true)
      setErrorMsg(null)
      await createAdminTeacher(token, {
        email: teacherEmail.trim(),
        name: teacherName.trim(),
        password: teacherPassword.trim(),
      })
      setCreatedTeacherCreds({
        name: teacherName.trim(),
        email: teacherEmail.trim(),
        password: teacherPassword.trim(),
      })
      setSuccessMsg(`Faculty member ${teacherName} (${teacherEmail}) provisioned successfully!`)
      setTeacherName('')
      setTeacherEmail('')
      setTeacherPassword('')
      loadUsers()
      loadOverview()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to provision faculty member.')
    } finally {
      setCreatingTeacher(false)
    }
  }

  // Handle Cautious Single-User Purge
  const handlePurgeUser = async (e: React.FormEvent) => {
    e.preventDefault()
    const target = purgeTargetEmail.trim().toLowerCase()
    const confirm = purgeConfirmEmail.trim().toLowerCase()

    if (!target || !confirm || !purgeAdminPassword.trim()) {
      setErrorMsg('Target email, confirmation email, and security password are required.')
      return
    }

    if (target !== confirm) {
      setErrorMsg('Confirmation email does not match the target email.')
      return
    }

    if (authUser?.email && target === authUser.email.toLowerCase()) {
      setErrorMsg('Administrators cannot delete their own account.')
      return
    }


    if (!window.confirm(`PERMANENT DELETION WARNING: Are you absolutely sure you want to permanently delete user ${target} and all their attempts, answers, and telemetry? This cannot be undone.`)) {
      return
    }

    try {
      setPurgingUser(true)
      setErrorMsg(null)
      const res = await purgeAdminUser(token, {
        target_email: target,
        admin_password: purgeAdminPassword.trim(),
      })
      setPurgeResult(res)
      setSuccessMsg(`User ${target} and all dependent records were permanently deleted.`)
      setPurgeTargetEmail('')
      setPurgeConfirmEmail('')
      setPurgeAdminPassword('')
      loadUsers()
      loadOverview()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to purge user.')
    } finally {
      setPurgingUser(false)
    }
  }

  // Handle Clean Teacher Workspace Execution
  const handleExecuteCleanWorkspace = async (e: React.FormEvent) => {
    e.preventDefault()
    if (cleanWorkspaceConfirmInput !== 'CONFIRM_CLEAN_TEACHER_WORKSPACE') {
      setErrorMsg("Confirmation code must be strictly 'CONFIRM_CLEAN_TEACHER_WORKSPACE'.")
      return
    }

    try {
      setCleaningWorkspace(true)
      setErrorMsg(null)
      const res = await executeCleanTeacherWorkspace(token, cleanWorkspaceConfirmInput)
      setCleanWorkspaceResult(res)
      setShowCleanWorkspaceModal(false)
      setCleanWorkspaceConfirmInput('')
      setSuccessMsg('Teacher workspace cleaned successfully! All students and attempts removed. Faculty & Admin preserved.')
      loadResetStatus()
      loadUsers()
      loadOverview()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Clean teacher workspace execution failed.')
    } finally {
      setCleaningWorkspace(false)
    }
  }

  const copyTeacherCredentials = () => {
    if (!createdTeacherCreds) return
    const text = `Quizdesk Faculty Portal Access\nName: ${createdTeacherCreds.name}\nEmail: ${createdTeacherCreds.email}\nInitial Password: ${createdTeacherCreds.password}\nPortal Link: ${window.location.origin}/teacher/login`
    navigator.clipboard.writeText(text)
    setCredsCopied(true)
    setTimeout(() => setCredsCopied(false), 3000)
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
          onClick={() => setActiveTab('purge')}
          className={`pb-3 px-1 border-b-2 transition-colors flex items-center space-x-2 ${
            activeTab === 'purge'
              ? 'border-rose-600 text-rose-700 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <UserX className="w-4 h-4 text-rose-500" />
          <span>Cautious Delete User</span>
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
          <RotateCcw className="w-4 h-4 text-rose-500" />
          <span>Guarded Reset & Workspace</span>
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

              <button
                type="button"
                onClick={() => {
                  setCreatedTeacherCreds(null)
                  setShowTeacherModal(true)
                }}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-sm transition-colors whitespace-nowrap"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>+ Onboard Faculty</span>
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
                              <div className="flex items-center justify-end space-x-2">
                                <button
                                  type="button"
                                  disabled={updatingUserId === u.id}
                                  onClick={() => handleToggleUserStatus(u)}
                                  className={`px-2.5 py-1 text-[11px] font-medium rounded transition-colors ${
                                    u.is_active
                                      ? 'text-slate-600 hover:bg-slate-100 border border-slate-200'
                                      : 'text-emerald-700 hover:bg-emerald-50 border border-emerald-300'
                                  }`}
                                >
                                  {updatingUserId === u.id
                                    ? 'Updating...'
                                    : u.is_active
                                    ? 'Deactivate'
                                    : 'Activate'}
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setPurgeTargetEmail(u.email)
                                    setPurgeConfirmEmail(u.email)
                                    setActiveTab('purge')
                                  }}
                                  className="px-2.5 py-1 text-[11px] font-medium text-rose-600 hover:bg-rose-50 border border-rose-200 rounded transition-colors flex items-center space-x-1"
                                  title="Permanently purge user and attempts"
                                >
                                  <Trash2 className="w-3 h-3" />
                                  <span>Purge</span>
                                </button>
                              </div>
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

      {/* TAB: CAUTIOUS DELETE USER */}
      {activeTab === 'purge' && (
        <div className="space-y-6">
          <div className="bg-white border border-rose-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 rounded-xl bg-rose-100 border border-rose-200 flex items-center justify-center text-rose-600 flex-shrink-0">
                <AlertOctagon className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h2 className="text-base font-bold text-slate-900">Cautious User & Record Purge</h2>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-rose-100 text-rose-700 border border-rose-200">
                    Irreversible
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
                  Safely and permanently purge a student or user account along with all dependent assessment records.
                  This cleans out student profiles, roster entries, exam attempts, autosaved answers, and proctoring
                  telemetry, and deletes their Supabase Auth record so they can be re-enrolled immediately if an
                  email or PRN typo occurred.
                </p>
              </div>
            </div>

            {/* Warning Callout */}
            <div className="p-4 bg-rose-50/80 border border-rose-200 rounded-lg text-xs space-y-2 text-rose-900">
              <div className="flex items-center space-x-2 font-semibold text-rose-800">
                <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                <span>Safeguards & Security Verification</span>
              </div>
              <ul className="list-disc pl-5 space-y-1 text-slate-700">
                <li>
                  <strong>Admin Self-Protection:</strong> Administrators cannot delete their own account or any other administrator.
                </li>
                <li>
                  <strong>Complete Cascade:</strong> All quiz submissions, proctoring alerts, and grade adjustments linked to this user are cleanly removed.
                </li>
                <li>
                  <strong>Supabase Auth Sync:</strong> The user's Supabase credentials are permanently cleared, allowing them to re-register with the correct email or PRN.
                </li>
                <li>
                  <strong>Mandatory Verification:</strong> Requires target email re-confirmation and administrative security password.
                </li>
              </ul>
            </div>

            {/* Purge Form */}
            <form onSubmit={handlePurgeUser} className="space-y-4 max-w-xl pt-2">
              <div>
                <label htmlFor="purge-email" className="block text-xs font-semibold text-slate-700 mb-1">
                  Target User Email to Delete
                </label>
                <input
                  id="purge-email"
                  type="email"
                  required
                  placeholder="e.g. 202401110045@mitaoe.ac.in"
                  value={purgeTargetEmail}
                  onChange={(e) => setPurgeTargetEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                />
              </div>

              <div>
                <label htmlFor="purge-confirm-email" className="block text-xs font-semibold text-slate-700 mb-1">
                  Re-type Target Email to Confirm
                </label>
                <input
                  id="purge-confirm-email"
                  type="email"
                  required
                  placeholder="Re-enter identical email address"
                  value={purgeConfirmEmail}
                  onChange={(e) => setPurgeConfirmEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                />
                {purgeTargetEmail && purgeConfirmEmail && purgeTargetEmail.toLowerCase() !== purgeConfirmEmail.toLowerCase() && (
                  <p className="text-[11px] text-rose-600 mt-1 font-medium">Emails do not match.</p>
                )}
              </div>

              <div>
                <label htmlFor="purge-admin-pass" className="block text-xs font-semibold text-slate-700 mb-1">
                  Administrative Security Password / Token
                </label>
                <div className="relative">
                  <input
                    id="purge-admin-pass"
                    type={showPurgePass ? 'text' : 'password'}
                    required
                    placeholder="Enter your admin account password or authorization token"
                    value={purgeAdminPassword}
                    onChange={(e) => setPurgeAdminPassword(e.target.value)}
                    className="w-full pl-3 pr-10 py-2 border border-slate-300 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPurgePass(!showPurgePass)}
                    className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
                  >
                    {showPurgePass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Verifies that only an authorized administrator can delete user data.
                </p>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={
                    purgingUser ||
                    !purgeTargetEmail.trim() ||
                    !purgeConfirmEmail.trim() ||
                    purgeTargetEmail.toLowerCase() !== purgeConfirmEmail.toLowerCase() ||
                    !purgeAdminPassword.trim()
                  }
                  className="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors shadow-sm"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>{purgingUser ? 'Purging User Records...' : 'Permanently Purge User Account'}</span>
                </button>
              </div>
            </form>

            {/* Last Execution Outcome */}
            {purgeResult && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-3">
                <div className="flex items-center space-x-2 text-emerald-700 font-semibold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{purgeResult.message}</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px] text-slate-700">
                  {Object.entries(purgeResult.cleared_records).map(([table, count]) => (
                    <div key={table} className="p-2 bg-white rounded border border-slate-200">
                      <div className="text-slate-500 text-[10px] capitalize">{table.replace(/_/g, ' ')}</div>
                      <div className="font-bold text-slate-900">{count} cleared</div>
                    </div>
                  ))}
                  <div className="p-2 bg-white rounded border border-slate-200">
                    <div className="text-slate-500 text-[10px]">Supabase Auth</div>
                    <div className="font-bold text-emerald-700">Purged</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: AUDIT TRAIL */}
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

      {/* TAB 5: GUARDED RESET & WORKSPACE */}
      {activeTab === 'reset' && (
        <div className="space-y-6">
          {/* Card 1: Clean Teacher Workspace (Testing Rehearsal) */}
          <div className="bg-white border border-indigo-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-100 border border-indigo-200 flex items-center justify-center text-indigo-600 flex-shrink-0">
                <RotateCcw className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h2 className="text-base font-bold text-slate-900">Clean Teacher Workspace (Testing Rehearsal)</h2>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-indigo-100 text-indigo-700 border border-indigo-200">
                    Preserves Faculty & Admin
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
                  Tailored specifically for teacher experimentation and trial testing. Clears all test candidate data
                  (student accounts, student profiles, roster assignments, attempts, answers, and test quizzes) while
                  strictly preserving all Teacher/Faculty accounts and Administrator accounts so instructors can
                  repeatedly run practice exams with a clean candidate slate.
                </p>
              </div>
            </div>

            <div className="p-4 bg-indigo-50/70 border border-indigo-200 rounded-lg text-xs space-y-2 text-indigo-950">
              <div className="flex items-center space-x-2 font-semibold text-indigo-900">
                <Info className="w-4 h-4 text-indigo-600" />
                <span>Rehearsal Wipe Policy</span>
              </div>
              <ul className="list-disc pl-5 space-y-1 text-slate-700">
                <li>
                  <strong>Teachers & Admins Safe:</strong> Teacher accounts, logins, and administrator profiles are NEVER deleted.
                </li>
                <li>
                  <strong>Candidate Reset:</strong> All test student accounts in PostgreSQL and Supabase Auth are purged so they can be re-enrolled cleanly.
                </li>
                <li>
                  <strong>Clean Slate:</strong> All test attempts, telemetry events, grade adjustments, and test quizzes are cleared.
                </li>
              </ul>
            </div>

            <div>
              {resetStatus?.can_reset ? (
                <button
                  type="button"
                  onClick={() => setShowCleanWorkspaceModal(true)}
                  className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors shadow-sm"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Initiate Clean Teacher Workspace</span>
                </button>
              ) : (
                <div className="p-3 bg-slate-100 border border-slate-200 rounded-lg text-xs text-slate-600 flex items-center space-x-2">
                  <Lock className="w-4 h-4 text-slate-500" />
                  <span>Clean workspace reset is currently disabled by system configuration.</span>
                </div>
              )}
            </div>

            {cleanWorkspaceResult && (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs space-y-2">
                <div className="flex items-center space-x-2 text-emerald-800 font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>{cleanWorkspaceResult.message}</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px] text-slate-700">
                  <div className="p-2 bg-white rounded border border-emerald-200">
                    <div className="text-slate-500 text-[10px]">Students Purged</div>
                    <div className="font-bold text-slate-900">{cleanWorkspaceResult.purged_students_count} removed</div>
                  </div>
                  <div className="p-2 bg-white rounded border border-emerald-200">
                    <div className="text-slate-500 text-[10px]">Teachers Preserved</div>
                    <div className="font-bold text-indigo-700">{cleanWorkspaceResult.preserved_teachers_count} intact</div>
                  </div>
                  {Object.entries(cleanWorkspaceResult.cleared_records).slice(0, 2).map(([table, count]) => (
                    <div key={table} className="p-2 bg-white rounded border border-emerald-200">
                      <div className="text-slate-500 text-[10px] capitalize">{table.replace(/_/g, ' ')}</div>
                      <div className="font-bold text-slate-900">{count} cleared</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Card 2: Factory Baseline Test Data Reset */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 rounded-xl bg-rose-100 flex items-center justify-center text-rose-600 flex-shrink-0">
                <Trash2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h2 className="text-base font-bold text-slate-900">Complete Assessment Data Wipe (Factory Baseline)</h2>
                <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
                  High-risk maintenance utility intended solely for developer testing and QA rehearsal.
                  Clears application assessment data (quizzes, immutable versions, question banks, roster
                  assignments, candidate attempts, answers, and telemetry) to return the environment to an
                  empty baseline. User accounts are preserved.
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

            {/* Action Trigger */}
            <div className="pt-2">
              {resetStatus?.can_reset ? (
                <button
                  type="button"
                  onClick={() => setShowResetModal(true)}
                  className="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Initiate Complete Test Data Reset</span>
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

      {/* MODAL 1: COMPLETE TEST DATA RESET CONFIRMATION */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center space-x-3 text-rose-600">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <h3 className="text-base font-bold text-slate-900">Confirm Complete Assessment Reset</h3>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              This action will permanently delete all quizzes, immutable versions, question banks,
              roster assignments, and candidate attempts across the entire system. Administrator and
              user accounts remain intact.
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

      {/* MODAL 2: CLEAN TEACHER WORKSPACE CONFIRMATION */}
      {showCleanWorkspaceModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center space-x-3 text-indigo-600">
              <RotateCcw className="w-6 h-6 flex-shrink-0" />
              <h3 className="text-base font-bold text-slate-900">Clean Teacher Workspace</h3>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              This will permanently delete all student accounts, profiles, roster entries, exam attempts,
              and test quizzes. <strong>Teacher and Admin accounts will remain completely intact.</strong>
            </p>

            <form onSubmit={handleExecuteCleanWorkspace} className="space-y-4 pt-2">
              <div>
                <label htmlFor="clean-workspace-code" className="block text-xs font-semibold text-slate-700 mb-1">
                  Type <span className="font-mono text-indigo-600 bg-indigo-50 px-1 py-0.5 rounded">CONFIRM_CLEAN_TEACHER_WORKSPACE</span> to verify:
                </label>
                <input
                  id="clean-workspace-code"
                  type="text"
                  required
                  value={cleanWorkspaceConfirmInput}
                  onChange={(e) => setCleanWorkspaceConfirmInput(e.target.value)}
                  placeholder="CONFIRM_CLEAN_TEACHER_WORKSPACE"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  disabled={cleaningWorkspace}
                  onClick={() => {
                    setShowCleanWorkspaceModal(false)
                    setCleanWorkspaceConfirmInput('')
                  }}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={cleaningWorkspace || cleanWorkspaceConfirmInput !== 'CONFIRM_CLEAN_TEACHER_WORKSPACE'}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>{cleaningWorkspace ? 'Cleaning Workspace...' : 'Execute Clean Workspace'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: ONBOARD FACULTY MEMBER */}
      {showTeacherModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2.5">
                <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Onboard Faculty Member</h3>
                  <p className="text-[11px] text-slate-500">Provision authorized educator account</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowTeacherModal(false)
                  setCreatedTeacherCreds(null)
                }}
                className="text-slate-400 hover:text-slate-700 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {createdTeacherCreds ? (
              <div className="space-y-4 pt-1">
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center space-x-2 text-emerald-800 font-semibold">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>Faculty Account Activated!</span>
                  </div>
                  <p className="text-slate-600 leading-relaxed">
                    This account is confirmed and ready for use immediately on the Faculty Portal.
                  </p>
                  <div className="mt-3 p-3 bg-white border border-emerald-200 rounded-lg font-mono text-[11px] space-y-1.5 text-slate-800">
                    <div>
                      <span className="text-slate-400">Name:</span> {createdTeacherCreds.name}
                    </div>
                    <div>
                      <span className="text-slate-400">Email:</span> {createdTeacherCreds.email}
                    </div>
                    <div>
                      <span className="text-slate-400">Initial Password:</span> {createdTeacherCreds.password}
                    </div>
                    <div className="text-[10px] text-indigo-600 pt-1">
                      Portal: {window.location.origin}/teacher/login
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-end space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={copyTeacherCredentials}
                    className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                  >
                    {credsCopied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{credsCopied ? 'Copied to Clipboard!' : 'Copy Credentials'}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowTeacherModal(false)
                      setCreatedTeacherCreds(null)
                    }}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition-colors"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleCreateTeacher} className="space-y-3.5 pt-1">
                <div>
                  <label htmlFor="teacher-name" className="block text-xs font-semibold text-slate-700 mb-1">
                    Full Name
                  </label>
                  <input
                    id="teacher-name"
                    type="text"
                    required
                    placeholder="e.g. Dr. Radhika Sharma"
                    value={teacherName}
                    onChange={(e) => setTeacherName(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label htmlFor="teacher-email" className="block text-xs font-semibold text-slate-700 mb-1">
                    Institutional Email Address
                  </label>
                  <input
                    id="teacher-email"
                    type="email"
                    required
                    placeholder="e.g. radhika.sharma@mitaoe.ac.in"
                    value={teacherEmail}
                    onChange={(e) => setTeacherEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label htmlFor="teacher-password" className="text-xs font-semibold text-slate-700">
                      Initial Password
                    </label>
                    <button
                      type="button"
                      onClick={generateRandomPassword}
                      className="text-[11px] text-indigo-600 hover:text-indigo-800 font-medium flex items-center space-x-1"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>Generate Secure</span>
                    </button>
                  </div>
                  <div className="relative">
                    <input
                      id="teacher-password"
                      type={showTeacherPass ? 'text' : 'password'}
                      required
                      minLength={6}
                      placeholder="Minimum 6 characters"
                      value={teacherPassword}
                      onChange={(e) => setTeacherPassword(e.target.value)}
                      className="w-full pl-3 pr-10 py-2 border border-slate-300 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowTeacherPass(!showTeacherPass)}
                      className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
                    >
                      {showTeacherPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">
                    The teacher can sign in immediately or reset password anytime via Faculty Portal.
                  </p>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    disabled={creatingTeacher}
                    onClick={() => setShowTeacherModal(false)}
                    className="px-3.5 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creatingTeacher}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5 shadow-sm"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>{creatingTeacher ? 'Provisioning Account...' : 'Provision Faculty Account'}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  )
}
