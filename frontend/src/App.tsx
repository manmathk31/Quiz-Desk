import React from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { Shell } from './components/layout/Shell'
import { Home } from './pages/Home'
import { Overview } from './pages/Overview'
import { NotFound } from './pages/NotFound'
import { Unauthorized } from './pages/Unauthorized'
import { RequireRole } from './components/auth/RequireRole'
import { StudentDashboard } from './pages/student/StudentDashboard'
import { ActiveAssessment } from './pages/student/ActiveAssessment'
import { AssessmentCompletion } from './pages/student/AssessmentCompletion'
import { TeacherPortalPlaceholder } from './pages/TeacherPortalPlaceholder'
import { QuestionBank } from './pages/teacher/QuestionBank'
import { QuizList } from './pages/teacher/QuizList'
import { QuizBuilder } from './pages/teacher/QuizBuilder'
import { QuizResults } from './pages/teacher/QuizResults'

import { StudentLogin } from './pages/auth/StudentLogin'
import { TeacherLogin } from './pages/auth/TeacherLogin'
import { TeacherForgotPassword } from './pages/auth/TeacherForgotPassword'
import { TeacherResetPassword } from './pages/auth/TeacherResetPassword'
import { AdminLogin } from './pages/auth/AdminLogin'
import { AdminDashboard } from './pages/admin/AdminDashboard'

/**
 * Intelligent login gateway:
 * Routes unauthenticated visitors or fallback redirections to the appropriate login portal:
 * - Admin routes (/admin/* or /status) -> /admin/login
 * - Faculty routes (/teacher/*) -> /teacher/login
 * - Student routes & default -> /student/login
 */
const LoginGateway: React.FC = () => {
  const location = useLocation()
  const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || ''

  if (from.startsWith('/admin') || from === '/status') {
    return <Navigate to="/admin/login" replace state={location.state} />
  }
  if (from.startsWith('/teacher')) {
    return <Navigate to="/teacher/login" replace state={location.state} />
  }
  return <Navigate to="/student/login" replace state={location.state} />
}

/**
 * Intelligent gateway for the root URL:
 * - Redirects authenticated students directly to their assessment dashboard.
 * - Redirects teachers directly to their quiz management list.
 * - Redirects administrators directly to the operational admin dashboard.
 * - Directs unauthenticated visitors to the primary student examination entrance.
 */
const RootGateway: React.FC = () => {
  const { session, role, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  if (!session) {
    return <Home />
  }

  if (role === 'student') {
    return <Navigate to="/student/portal" replace />
  }

  if (role === 'teacher') {
    return <Navigate to="/teacher/quizzes" replace />
  }

  if (role === 'admin') {
    return <Navigate to="/admin/dashboard" replace />
  }

  return <Home />
}

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Shell>
          <Routes>
            {/* Intelligent Root Gateway & Role-Segregated Entry Routes */}
            <Route path="/" element={<RootGateway />} />
            <Route path="/login" element={<LoginGateway />} />
            <Route path="/student/login" element={<StudentLogin />} />
            <Route path="/teacher/login" element={<TeacherLogin />} />
            <Route path="/teacher/forgot-password" element={<TeacherForgotPassword />} />
            <Route path="/teacher/reset-password" element={<TeacherResetPassword />} />
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            {/* Protected Technical & System Diagnostics Routes (Administrator Only) */}
            <Route
              path="/status"
              element={
                <RequireRole allowedRoles={['admin']}>
                  <Overview />
                </RequireRole>
              }
            />
            <Route path="/admin/overview" element={<Navigate to="/status" replace />} />

            {/* Student Role-Protected Routes */}
            <Route
              path="/student/portal"
              element={
                <RequireRole allowedRoles={['student']}>
                  <StudentDashboard />
                </RequireRole>
              }
            />
            <Route
              path="/student/assessments/:attemptId"
              element={
                <RequireRole allowedRoles={['student']}>
                  <ActiveAssessment />
                </RequireRole>
              }
            />
            <Route
              path="/student/assessments/:attemptId/completed"
              element={
                <RequireRole allowedRoles={['student']}>
                  <AssessmentCompletion />
                </RequireRole>
              }
            />
            <Route
              path="/teacher/portal"
              element={
                <RequireRole allowedRoles={['teacher', 'admin']}>
                  <TeacherPortalPlaceholder />
                </RequireRole>
              }
            />
            <Route
              path="/teacher/question-bank"
              element={
                <RequireRole allowedRoles={['teacher', 'admin']}>
                  <QuestionBank />
                </RequireRole>
              }
            />
            <Route
              path="/teacher/quizzes"
              element={
                <RequireRole allowedRoles={['teacher', 'admin']}>
                  <QuizList />
                </RequireRole>
              }
            />
            <Route
              path="/teacher/quizzes/:quizId"
              element={
                <RequireRole allowedRoles={['teacher', 'admin']}>
                  <QuizBuilder />
                </RequireRole>
              }
            />
            <Route
              path="/teacher/quizzes/:quizId/results"
              element={
                <RequireRole allowedRoles={['teacher', 'admin']}>
                  <QuizResults />
                </RequireRole>
              }
            />

            {/* Admin Operational Portal Route */}
            <Route
              path="/admin/dashboard"
              element={
                <RequireRole allowedRoles={['admin']}>
                  <AdminDashboard />
                </RequireRole>
              }
            />

            {/* Fallback 404 Route */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Shell>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
