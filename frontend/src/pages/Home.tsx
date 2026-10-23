import React from 'react'
import { Link } from 'react-router-dom'
import { 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  Clock, 
  BookOpen,
  Monitor
} from 'lucide-react'

export const Home: React.FC = () => {
  return (
    <div className="space-y-12 py-4">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-850 to-blue-950 text-white rounded-2xl p-8 sm:p-12 border border-slate-800 shadow-xl">
        <div className="relative z-10 max-w-3xl">
          {/* College Tag */}
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-blue-500/10 border border-blue-400/20 rounded-full text-xs font-semibold text-blue-300 mb-6 backdrop-blur-sm">
            <span>MIT Academy of Engineering</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Online Quiz Platform
          </h1>

          <p className="mt-4 text-base sm:text-lg text-slate-300 leading-relaxed font-normal max-w-2xl">
            A simple, secure platform to take your course quizzes and assessments online with automatic saving and clear countdown timers.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              to="/student/login"
              className="inline-flex items-center justify-center px-6 py-3.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-600/30 transition-all hover:scale-[1.02] duration-150"
            >
              <span>Student Sign In</span>
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>

            <div className="inline-flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/60 px-3.5 py-3 rounded-xl border border-slate-700/50">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Online & Ready</span>
            </div>
          </div>
        </div>

        {/* Ambient subtle glow */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>
      </section>

      {/* General Features Cards */}
      <section aria-labelledby="platform-features-title">
        <div className="text-center max-w-xl mx-auto mb-8">
          <h2 id="platform-features-title" className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            How It Works
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Everything you need for a smooth quiz experience
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-11 h-11 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4">
              <BookOpen className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">College Account Access</h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
              Log in with your college email. Quizzes created by your professors will appear directly on your student dashboard.
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 mb-4">
              <Clock className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">Auto-Saved Answers</h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
              Every answer you select saves automatically. Even if your internet flickers, you can simply reconnect and continue.
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-11 h-11 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">Secure & Focused</h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
              A distraction-free testing screen with a clear timer keeps everyone on track and gives every student a fair test environment.
            </p>
          </div>
        </div>
      </section>

      {/* Student Instructions */}
      <section className="bg-slate-50 border border-slate-200 rounded-2xl p-6 sm:p-8">
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
            <Monitor className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Instructions for Students</h2>
            <p className="text-xs text-slate-500">Quick tips before you start your quiz</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-700">
          <div className="flex items-start space-x-2.5 bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>Use an updated desktop browser like Google Chrome or Microsoft Edge.</span>
          </div>

          <div className="flex items-start space-x-2.5 bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>Have your college email and PRN / Roll Number ready.</span>
          </div>

          <div className="flex items-start space-x-2.5 bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>Stay focused on the quiz window while answering questions.</span>
          </div>

          <div className="flex items-start space-x-2.5 bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>If your internet disconnects, your progress is saved—reconnect to resume.</span>
          </div>
        </div>
      </section>
    </div>
  )
}
