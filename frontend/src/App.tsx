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
import { StudentPortalPlaceholder } from './pages/StudentPortalPlaceholder'
import { TeacherPortalPlaceholder } from './pages/TeacherPortalPlaceholder'
import { QuestionBank } from './pages/teacher/QuestionBank'
import { QuizList } from './pages/teacher/QuizList'
import { QuizBuilder } from './pages/teacher/QuizBuilder'

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Shell>
          <Routes>
            {/* Public Institutional Information Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/status" element={<Overview />} />
            <Route path="/login" element={<Login />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            {/* Role-Protected Routes */}
            <Route
              path="/student/portal"
              element={
                <RequireRole allowedRoles={['student']}>
                  <StudentPortalPlaceholder />
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


            {/* Fallback 404 Route */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Shell>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
