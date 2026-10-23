import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { CheckCircle2, Clock, ArrowRight, ShieldCheck } from 'lucide-react'

export const AssessmentCompletion: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const autoExpired = location.state?.autoExpired || false

  return (
    <div className="max-w-xl mx-auto my-16 px-4 text-slate-900">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 mx-auto mb-4">
          <CheckCircle2 className="w-8 h-8" />
        </div>

        <h1 className="text-xl font-bold text-slate-900">
          {autoExpired ? 'Assessment Finalized (Time Expired)' : 'Assessment Submitted Successfully'}
        </h1>

        <p className="text-xs text-slate-500 mt-2 max-w-md mx-auto leading-relaxed">
          {autoExpired
            ? 'The assessment deadline elapsed. Your saved answers were automatically submitted for evaluation.'
            : 'Your attempt has been finalized on the server and safely recorded for automated evaluation.'}
        </p>

        <div className="my-6 p-4 bg-slate-50 border border-slate-200 rounded-xl text-left text-xs text-slate-600 space-y-3">
          <div className="flex items-start space-x-2.5">
            <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-800">Server Verification:</span>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Session state, answers, and telemetry logs are cryptographically sealed in the database.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-2.5">
            <Clock className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-800">Result Release Policy:</span>
              <p className="text-[11px] text-slate-500 mt-0.5">
                In accordance with college examination guidelines, score breakdowns and answer reviews are withheld until released by your instructor.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => navigate('/student/portal')}
          className="w-full sm:w-auto px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm inline-flex items-center justify-center space-x-2"
        >
          <span>Return to Student Portal</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
