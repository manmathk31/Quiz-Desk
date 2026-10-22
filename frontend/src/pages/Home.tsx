import React from 'react'
import { Link } from 'react-router-dom'
import { 
  CheckCircle2, 
  FileCheck2, 
  Users, 
  ShieldCheck, 
  Clock, 
  ArrowRight,
  ExternalLink
} from 'lucide-react'

export const Home: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Platform Banner / Hero */}
      <section className="bg-white border border-slate-200 rounded-lg p-6 sm:p-8" aria-labelledby="platform-title">
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 font-medium mb-4">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Architecture & Environment Baseline Verified</span>
          </div>
          <h1 id="platform-title" className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Institutional Quiz & Assessment Platform
          </h1>
          <p className="mt-3 text-base text-slate-600 leading-relaxed">
            Quizdesk is an academic examination platform built for strict integrity, reliable concurrent assessment delivery, and server-authoritative evaluation.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/status"
              className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 transition-colors"
            >
              System Health & Diagnostics
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 transition-colors"
            >
              FastAPI Swagger Docs
              <ExternalLink className="w-3.5 h-3.5 ml-1.5 text-slate-400" />
            </a>
          </div>
        </div>
      </section>

      {/* Core Architectural Pillars */}
      <section aria-labelledby="pillars-heading">
        <h2 id="pillars-heading" className="text-lg font-semibold text-slate-900 mb-4">
          Core Workflows & Boundaries (Confirmed Design)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Teacher Experience */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 mb-3">
                <FileCheck2 className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-slate-900">Teacher Authoring</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Single/Multi MCQs and True/False questions. Bulk CSV import with error pre-validation, mark weighting, and immutable quiz versioning.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-xs font-medium text-slate-500">
              Scheduled Phase 4
            </div>
          </div>

          {/* Card 2: Student Experience */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 mb-3">
                <Clock className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-slate-900">Student Assessment</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Distraction-free interface with server-authoritative timer, safe background autosave, reconnect recovery, and transparent tab-switch telemetry.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-xs font-medium text-slate-500">
              Scheduled Phase 6
            </div>
          </div>

          {/* Card 3: Roster & Integrity */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 mb-3">
                <Users className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-slate-900">Roster & Auditability</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Per-quiz CSV assignment (<code className="text-xs bg-slate-100 px-1 py-0.5 rounded font-mono">prn,name,email,division</code>), withheld results until teacher release, and audited grade changes.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-xs font-medium text-slate-500">
              Scheduled Phase 5 & 7
            </div>
          </div>
        </div>
      </section>

      {/* Presentation Shell: Sample Assessment Portal Table (Illustrative UI Pattern) */}
      <section className="bg-white border border-slate-200 rounded-lg overflow-hidden" aria-labelledby="sample-schedule">
        <div className="px-6 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 id="sample-schedule" className="text-base font-semibold text-slate-900">
              Assessment Portal Table Layout
            </h2>
            <p className="text-xs text-slate-500">
              Target design pattern for scheduled assessments (Presentation Shell)
            </p>
          </div>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            UI Layout Sample
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-700">
              <tr>
                <th scope="col" className="px-6 py-3 font-medium">Code</th>
                <th scope="col" className="px-6 py-3 font-medium">Assessment Title</th>
                <th scope="col" className="px-6 py-3 font-medium">Schedule Window</th>
                <th scope="col" className="px-6 py-3 font-medium">Duration</th>
                <th scope="col" className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              <tr className="hover:bg-slate-50/50">
                <td className="px-6 py-3.5 font-mono text-xs font-semibold text-slate-900">CS-301</td>
                <td className="px-6 py-3.5 font-medium text-slate-900">Operating Systems Midterm Assessment</td>
                <td className="px-6 py-3.5 text-slate-600 text-xs">Oct 28, 10:00 AM - 12:00 PM</td>
                <td className="px-6 py-3.5 text-slate-600 text-xs">60 min</td>
                <td className="px-6 py-3.5">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                    Scheduled
                  </span>
                </td>
              </tr>
              <tr className="hover:bg-slate-50/50">
                <td className="px-6 py-3.5 font-mono text-xs font-semibold text-slate-900">CS-304</td>
                <td className="px-6 py-3.5 font-medium text-slate-900">Database Management Systems Quiz 1</td>
                <td className="px-6 py-3.5 text-slate-600 text-xs">Oct 30, 02:00 PM - 03:30 PM</td>
                <td className="px-6 py-3.5 text-slate-600 text-xs">45 min</td>
                <td className="px-6 py-3.5">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                    Draft
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Security & Reliability Callout */}
      <section className="bg-slate-900 text-slate-200 rounded-lg p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start space-x-3.5">
          <div className="p-2 bg-slate-800 rounded border border-slate-700 text-blue-400 mt-0.5 sm:mt-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-base">Server-Authoritative Evaluation</h3>
            <p className="text-slate-400 text-sm mt-0.5">
              Answer keys remain strictly protected on the backend. Attempt deadlines are enforced by server timestamps.
            </p>
          </div>
        </div>
        <div className="text-xs font-mono text-slate-400 bg-slate-800/80 px-3 py-1.5 rounded border border-slate-700 whitespace-nowrap">
          DEC-008 &bull; DEC-009 Confirmed
        </div>
      </section>
    </div>
  )
}
