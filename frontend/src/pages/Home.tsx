import React from 'react'
import { Link } from 'react-router-dom'
import { 
  GraduationCap, 
  ShieldCheck, 
  Clock, 
  ArrowRight, 
  CheckCircle2, 
  Sparkles,
  Laptop
} from 'lucide-react'

export const Home: React.FC = () => {
  return (
    <div className="space-y-12 py-4">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-850 to-blue-950 text-white rounded-2xl p-8 sm:p-12 border border-slate-800 shadow-xl">
        <div className="relative z-10 max-w-3xl">
          {/* Institutional Badge */}
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-blue-500/10 border border-blue-400/20 rounded-full text-xs font-semibold text-blue-300 mb-6 backdrop-blur-sm">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>MIT Academy of Engineering • Official Examination Portal</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Digital Assessment & Examination Platform
          </h1>

          <p className="mt-4 text-base sm:text-lg text-slate-300 leading-relaxed font-normal max-w-2xl">
            Quizdesk delivers secure, server-timed academic assessments, continuous evaluations, and midterm examinations with automated autosaving and academic integrity.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              to="/student/login"
              className="inline-flex items-center justify-center px-6 py-3.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-600/30 transition-all hover:scale-[1.02] duration-150"
            >
              <span>Enter Student Examination Portal</span>
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>

            <div className="inline-flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/60 px-3.5 py-3 rounded-xl border border-slate-700/50">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Proctored • Autosave Active</span>
            </div>
          </div>
        </div>

        {/* Decorative subtle ambient glow */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>
      </section>

      {/* 3 Core Examination Pillars */}
      <section aria-labelledby="exam-pillars-title">
        <div className="text-center max-w-xl mx-auto mb-8">
          <h2 id="exam-pillars-title" className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Institutional Exam Architecture
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Engineered for fair, resilient, and distraction-free student evaluation
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Pillar 1 */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-11 h-11 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4">
              <GraduationCap className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">Institutional Identity</h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
              Authenticate using your official college credentials (<code className="text-[11px] font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-700">@mitaoe.ac.in</code>). Assessment access is mapped strictly to your registered division and PRN.
            </p>
          </div>

          {/* Pillar 2 */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 mb-4">
              <Clock className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">Server-Synchronized Timing</h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
              Assessment countdowns are authoritative and synchronized with the cloud server. Responses autosave in real-time with resilient reconnect recovery.
            </p>
          </div>

          {/* Pillar 3 */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-11 h-11 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">Academic Integrity Guard</h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
              Continuous proctoring runs in a dedicated fullscreen container with transparent tab-switch and focus monitoring to maintain evaluation parity.
            </p>
          </div>
        </div>
      </section>

      {/* Student Examination Day Instructions */}
      <section className="bg-slate-50 border border-slate-200 rounded-2xl p-6 sm:p-8">
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
            <Laptop className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Student Examination Guidelines</h2>
            <p className="text-xs text-slate-500">Please review before joining your scheduled examination</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-700">
          <div className="flex items-start space-x-2.5 bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>Use an updated desktop browser (Google Chrome or Microsoft Edge recommended).</span>
          </div>

          <div className="flex items-start space-x-2.5 bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>Keep your registered PRN / Roll Number and college email ready for verification.</span>
          </div>

          <div className="flex items-start space-x-2.5 bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>Do not exit fullscreen mode or switch browser tabs during an active quiz session.</span>
          </div>

          <div className="flex items-start space-x-2.5 bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>In the event of accidental disconnection, your answers are saved on the server—simply re-login to resume.</span>
          </div>
        </div>
      </section>
    </div>
  )
}
