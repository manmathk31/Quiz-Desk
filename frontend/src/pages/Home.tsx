import React from 'react'
import { Link } from 'react-router-dom'
import { 
  ArrowRight, 
  CheckCircle2, 
  Clock, 
  Sparkles,
  Zap, 
  Layers, 
  ShieldCheck,
  ChevronRight,
  BookOpen
} from 'lucide-react'

export const Home: React.FC = () => {
  return (
    <div className="space-y-16 py-4">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white rounded-3xl p-8 sm:p-12 lg:p-16 border border-slate-800 shadow-2xl">
        {/* Subtle Ambient Background Accents */}
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Column: Pitch & Action */}
          <div className="lg:col-span-7 space-y-6">
            {/* College Pill Badge */}
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 bg-blue-500/10 border border-blue-400/25 rounded-full text-xs font-semibold text-blue-300 backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>MIT Academy of Engineering</span>
            </div>

            <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-white leading-[1.1]">
              Assessments <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-300">
                made seamless.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-300 leading-relaxed font-normal max-w-xl">
              Take your scheduled coursework quizzes in a clean, distraction-free environment. 
              Sub-second autosave, real-time timekeeping, and immediate question navigation.
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-4">
              <Link
                to="/student/login"
                className="group inline-flex items-center justify-center px-6 py-3.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-600/30 transition-all duration-150 hover:scale-[1.02]"
              >
                <span>Take Assessment</span>
                <ArrowRight className="w-4 h-4 ml-2 transition-transform duration-150 group-hover:translate-x-1" />
              </Link>

              <div className="inline-flex items-center space-x-2 text-xs text-slate-400 bg-slate-900/80 px-4 py-3 rounded-xl border border-slate-800">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Active Testing Environment</span>
              </div>
            </div>

            <div className="text-xs text-slate-400 flex items-center space-x-2 pt-1">
              <span>Use your college credentials</span>
              <span>•</span>
              <span className="font-mono text-slate-300 text-[11px]">@mitaoe.ac.in</span>
            </div>
          </div>

          {/* Right Column: Live Quiz UI Preview Card */}
          <div className="lg:col-span-5">
            <div className="bg-slate-900/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl backdrop-blur-xl relative overflow-hidden">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80"></span>
                  <span className="text-xs font-mono text-slate-400 pl-1">Live Session</span>
                </div>
                <div className="flex items-center space-x-1.5 px-2.5 py-1 bg-emerald-950/60 border border-emerald-800/50 rounded-md text-[11px] font-mono text-emerald-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                  <span>Synced</span>
                </div>
              </div>

              <div className="pt-5 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                    Question 04 of 20
                  </span>
                  <div className="flex items-center space-x-1 text-xs font-mono text-slate-300 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                    <Clock className="w-3 h-3 text-amber-400" />
                    <span>38:15 left</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-100">
                    Which data structure provides O(1) average-case time complexity for lookups?
                  </p>
                </div>

                {/* Option Snippets */}
                <div className="space-y-2 text-xs">
                  <div className="p-2.5 rounded-lg border border-slate-800 bg-slate-800/40 text-slate-300 flex items-center justify-between">
                    <span>A. Binary Search Tree</span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-blue-500/60 bg-blue-900/30 text-white font-medium flex items-center justify-between">
                    <span>B. Hash Table</span>
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-800 bg-slate-800/40 text-slate-300 flex items-center justify-between">
                    <span>C. Linked List</span>
                  </div>
                </div>

                {/* Autosave Footer */}
                <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60">
                  <span className="flex items-center text-emerald-400">
                    <CheckCircle2 className="w-3 h-3 mr-1" />
                    Response saved to cloud
                  </span>
                  <span className="font-mono text-slate-500">PRN: Verified</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Product Pillars: Pitching Value */}
      <section aria-labelledby="features-headline" className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 id="features-headline" className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Built for engineering coursework
          </h2>
          <p className="text-sm sm:text-base text-slate-600">
            Engineered from the ground up for high reliability and zero exam day friction.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="group bg-white border border-slate-200 rounded-2xl p-7 shadow-xs hover:shadow-xl hover:border-blue-200 transition-all duration-200 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Zero-Config Access</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                No entry PINs or access codes. Quizzes assigned to your division and PRN appear on your dashboard automatically.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center text-xs font-semibold text-blue-600">
              <span>Automatic course sync</span>
              <ChevronRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-1" />
            </div>
          </div>

          {/* Card 2 */}
          <div className="group bg-white border border-slate-200 rounded-2xl p-7 shadow-xs hover:shadow-xl hover:border-emerald-200 transition-all duration-200 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
                <Zap className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Continuous Autosave</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Every click saves immediately. If your Wi-Fi blips or your tab reloads, rejoin instantly and resume where you left off.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center text-xs font-semibold text-emerald-600">
              <span>Zero lost answers</span>
              <ChevronRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-1" />
            </div>
          </div>

          {/* Card 3 */}
          <div className="group bg-white border border-slate-200 rounded-2xl p-7 shadow-xs hover:shadow-xl hover:border-indigo-200 transition-all duration-200 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Distraction-Free Focus</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                A clean, uncluttered interface with an interactive question grid and authoritative countdown timer keeps you in the zone.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center text-xs font-semibold text-indigo-600">
              <span>Fair & equal testing</span>
              <ChevronRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-1" />
            </div>
          </div>
        </div>
      </section>

      {/* 3 Simple Steps to Take a Quiz */}
      <section className="bg-slate-900 text-white rounded-3xl p-8 sm:p-12 border border-slate-800 shadow-xl">
        <div className="max-w-2xl mb-8">
          <h2 className="text-2xl font-bold tracking-tight text-white">
            How to take your assessment
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Three simple steps to complete your scheduled quiz
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-800/70 border border-slate-700/60 rounded-2xl p-6 space-y-3">
            <span className="font-mono text-2xl font-black text-blue-400">01</span>
            <h3 className="text-base font-semibold text-white">Sign In with College ID</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Authenticate using your registered college email. Your dashboard shows all available tests for your class.
            </p>
          </div>

          <div className="bg-slate-800/70 border border-slate-700/60 rounded-2xl p-6 space-y-3">
            <span className="font-mono text-2xl font-black text-indigo-400">02</span>
            <h3 className="text-base font-semibold text-white">Review & Launch</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Check assessment rules, duration, and question count on the readiness screen, then launch into focus mode.
            </p>
          </div>

          <div className="bg-slate-800/70 border border-slate-700/60 rounded-2xl p-6 space-y-3">
            <span className="font-mono text-2xl font-black text-emerald-400">03</span>
            <h3 className="text-base font-semibold text-white">Review & Submit</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Use the question navigator to verify your answers, then hit Submit before the authoritative timer concludes.
            </p>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <BookOpen className="w-4 h-4 text-blue-400 shrink-0" />
            <span>Ready for your test? Enter with your college account.</span>
          </div>

          <Link
            to="/student/login"
            className="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-md transition-all hover:scale-[1.02]"
          >
            <span>Take Assessment</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </section>
    </div>
  )
}
