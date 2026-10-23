import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { Shell } from './components/layout/Shell'
import { Home } from './pages/Home'
import { Overview } from './pages/Overview'
import { NotFound } from './pages/NotFound'
import { Login } from './pages/Login'
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

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Shell>
          <Routes>
            {/* Public Institutional Information & Portal Entry Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/status" element={<Overview />} />
            <Route path="/login" element={<Login />} />
            <Route path="/student/login" element={<StudentLogin />} />
            <Route path="/teacher/login" element={<TeacherLogin />} />
            <Route path="/teacher/forgot-password" element={<TeacherForgotPassword />} />
            <Route path="/teacher/reset-password" element={<TeacherResetPassword />} />
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

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
