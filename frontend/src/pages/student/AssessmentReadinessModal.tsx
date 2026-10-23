import React, { useState, useEffect } from 'react'
import {
  Shield,
  Clock,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Maximize,
  Copy,
  Sliders,
  ExternalLink,
  Loader2,
  X,
  BellOff,
  Laptop,
} from 'lucide-react'
import { fetchAssessmentReadiness } from '../../services/assessmentApi'
import type { AssessmentReadiness } from '../../types/assessment'

interface AssessmentReadinessModalProps {
  quizId: string
  token: string
  isOpen: boolean
  onClose: () => void
  onConfirmStart: () => Promise<void>;
}

export const AssessmentReadinessModal: React.FC<AssessmentReadinessModalProps> = ({
  quizId,
  token,
  isOpen,
  onClose,
  onConfirmStart,
}) => {
  const [readiness, setReadiness] = useState<AssessmentReadiness | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isAcknowledged, setIsAcknowledged] = useState(false)
  const [isStarting, setIsStarting] = useState(false)

  // Browser capability check state
  const [fullscreenSupported, setFullscreenSupported] = useState(true)
  const [visibilitySupported, setVisibilitySupported] = useState(true)

  useEffect(() => {
    if (!isOpen || !quizId || !token) return

    setIsLoading(true)
    setError(null)
    setIsAcknowledged(false)
    setIsStarting(false)

    // Check client capabilities
    setFullscreenSupported(
      typeof document !== 'undefined' &&
        !!(
          document.fullscreenEnabled ||
          (document as unknown as { webkitFullscreenEnabled?: boolean }).webkitFullscreenEnabled
        )
    )
    setVisibilitySupported(typeof document !== 'undefined' && 'visibilityState' in document)

    fetchAssessmentReadiness(token, quizId)
      .then((data) => setReadiness(data))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load readiness details.'))
      .finally(() => setIsLoading(false))
  }, [isOpen, quizId, token])

  if (!isOpen) return null

  const handleStartAssessment = async () => {
    if (!isAcknowledged || isStarting) return
    setIsStarting(true)

    try {
      // If fullscreen required and supported, request it synchronously during user click handler
      if (readiness?.require_fullscreen && fullscreenSupported && document.documentElement.requestFullscreen) {
        try {
          if (!document.fullscreenElement) {
            await document.documentElement.requestFullscreen()
          }
        } catch {
          // Gracefully continue even if browser restricts fullscreen
        }
      }

      await onConfirmStart()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to launch assessment session.')
      setIsStarting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600/30 text-blue-400 flex items-center justify-center border border-blue-500/30">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-tight">Assessment Rules & Device Readiness</h2>
              <p className="text-[11px] text-slate-400">Institutional Examination Integrity & Pre-flight Verification</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isStarting}
            className="text-slate-400 hover:text-white p-1 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 max-h-[75vh] overflow-y-auto space-y-5 text-xs text-slate-700">
          {isLoading ? (
            <div className="py-12 text-center text-slate-500 flex flex-col items-center space-y-2">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <span>Verifying assessment eligibility and proctoring parameters...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start space-x-3 text-red-800">
              <XCircle className="w-5 h-5 shrink-0 text-red-600 mt-0.5" />
              <div>
                <p className="font-semibold">Unable to Proceed</p>
                <p className="mt-0.5 text-xs text-red-700">{error}</p>
              </div>
            </div>
          ) : readiness ? (
            <>
              {/* Quiz Overview Header Card */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                    {readiness.course_code}
                  </span>
                  <span className="text-[11px] text-slate-500 font-medium">
                    Attempts Used: {readiness.attempts_taken} / {readiness.max_attempts}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 leading-snug">{readiness.quiz_title}</h3>
                {readiness.description && (
                  <p className="text-xs text-slate-600 leading-relaxed">{readiness.description}</p>
                )}
                <div className="pt-2 border-t border-slate-200 flex flex-wrap items-center gap-4 text-slate-600 font-medium">
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>Duration: {readiness.duration_minutes} Minutes</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
                    <span>Backtracking: {readiness.allow_backtracking ? 'Allowed' : 'Disabled'}</span>
                  </span>
                </div>
              </div>

              {/* Proctoring Policy & Penalties Grid */}
              <div className="space-y-3">
                <h4 className="font-bold text-slate-900 flex items-center space-x-1.5 text-xs uppercase tracking-wide">
                  <Sliders className="w-3.5 h-3.5 text-blue-600" />
                  <span>Configured Proctoring Controls & Penalties</span>
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {/* Fullscreen policy */}
                  <div className="p-3 bg-white border border-slate-200 rounded-xl flex items-start space-x-2.5">
                    <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
                      <Maximize className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">
                        Fullscreen: {readiness.require_fullscreen ? 'Enforced' : 'Optional'}
                      </p>
                      <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
                        {readiness.require_fullscreen
                          ? 'Must remain in fullscreen throughout. Exits are logged and penalized.'
                          : 'Fullscreen is recommended but not mandatory.'}
                      </p>
                    </div>
                  </div>

                  {/* Clipboard policy */}
                  <div className="p-3 bg-white border border-slate-200 rounded-xl flex items-start space-x-2.5">
                    <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 mt-0.5">
                      <Copy className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">
                        Copy / Paste: {readiness.enable_copy_paste_restriction ? 'Restricted' : 'Permitted'}
                      </p>
                      <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
                        {readiness.enable_copy_paste_restriction
                          ? 'Copying question prompts and pasting answers are blocked and recorded.'
                          : 'Clipboard actions are unconstrained.'}
                      </p>
                    </div>
                  </div>

                  {/* Tab switches */}
                  <div className="p-3 bg-white border border-slate-200 rounded-xl flex items-start space-x-2.5">
                    <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0 mt-0.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">Tab & Focus Telemetry</p>
                      <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
                        Leaving the browser tab or switching application focus is monitored.
                      </p>
                    </div>
                  </div>

                  {/* DevTools shortcuts */}
                  <div className="p-3 bg-white border border-slate-200 rounded-xl flex items-start space-x-2.5">
                    <div className="w-7 h-7 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center shrink-0 mt-0.5">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">Developer Shortcuts</p>
                      <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
                        Developer console shortcuts (F12, Ctrl+Shift+I) are intercepted and logged.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Penalty Formula Banner */}
                <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 space-y-1.5">
                  <div className="font-semibold flex items-center space-x-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>Authoritative Penalty Calculation Rule</span>
                  </div>
                  <ul className="list-disc pl-5 space-y-1 text-[11px] text-amber-800">
                    <li>
                      <strong>Free Violation Allowance:</strong> {readiness.free_violation_allowance} incident(s) allowed
                      without penalty.
                    </li>
                    <li>
                      <strong>Deduction Rate:</strong> {readiness.violation_penalty_marks} mark(s) deducted per chargeable
                      incident once the allowance is exceeded.
                    </li>
                    <li>
                      <strong>Cumulative Maximum Deduction:</strong> Capped at {readiness.max_proctoring_deduction} marks
                      total (never exceeds candidate earned score).
                    </li>
                  </ul>
                </div>
              </div>

              {/* Device & Environment Readiness Checklist */}
              <div className="space-y-3">
                <h4 className="font-bold text-slate-900 flex items-center space-x-1.5 text-xs uppercase tracking-wide">
                  <Laptop className="w-3.5 h-3.5 text-blue-600" />
                  <span>Device & Environment Readiness Check</span>
                </h4>

                <div className="space-y-2 bg-slate-50 border border-slate-200 rounded-xl p-3.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center space-x-2">
                      {visibilitySupported ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                      <span>Browser Capability (HTML5 & Visibility API)</span>
                    </span>
                    <span className="font-semibold text-emerald-700">Supported</span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center space-x-2">
                      {fullscreenSupported ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-amber-600" />
                      )}
                      <span>Browser Fullscreen API</span>
                    </span>
                    <span className={fullscreenSupported ? 'font-semibold text-emerald-700' : 'font-semibold text-amber-700'}>
                      {fullscreenSupported ? 'Supported' : 'Limited'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Assessment Server Connectivity & Synchronization</span>
                    </span>
                    <span className="font-semibold text-emerald-700">Connected</span>
                  </div>
                </div>

                {/* Environment Advice */}
                <div className="p-3 bg-blue-50/60 border border-blue-200 rounded-xl text-blue-900 flex items-start space-x-2.5">
                  <BellOff className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                  <div className="text-[11px] leading-relaxed">
                    <strong>Candidate Advisory:</strong> Please turn on <em>Do Not Disturb</em> on your operating system,
                    close background messaging tabs, and avoid multi-finger touchpad swipes or system shortcuts that cause
                    accidental window focus loss. Browser monitoring detects page departure, not external OS internals.
                  </div>
                </div>
              </div>

              {/* Student Explicit Acknowledgement */}
              <label className="flex items-start space-x-2.5 pt-2 border-t border-slate-200 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={isAcknowledged}
                  onChange={(e) => setIsAcknowledged(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span className="text-xs text-slate-800 leading-normal font-medium">
                  I confirm that I have reviewed the examination duration, navigation policies, and proctoring rules.
                  I agree to take this examination under institutional academic integrity standards.
                </span>
              </label>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <button
            onClick={onClose}
            disabled={isStarting}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition-colors disabled:opacity-50"
          >
            Cancel & Return
          </button>

          <button
            onClick={handleStartAssessment}
            disabled={!isAcknowledged || isStarting || !readiness?.can_start}
            className="px-5 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-2 shadow-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isStarting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Launching Assessment...</span>
              </>
            ) : (
              <>
                <Shield className="w-3.5 h-3.5" />
                <span>
                  {readiness?.has_active_attempt ? 'Resume Assessment' : 'Confirm & Enter Assessment'}
                </span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
