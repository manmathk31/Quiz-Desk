import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  fetchAttemptContent,
  autosaveAnswer,
  sendTelemetry,
  submitAttempt,
} from '../../services/assessmentApi'
import type { AttemptContent, SanitizedQuestion } from '../../types/assessment'
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flag,
  ArrowLeft,
  ArrowRight,
  Send,
  RefreshCw,
  AlertOctagon,
  Check,
  Shield,
} from 'lucide-react'

export const ActiveAssessment: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>()
  const { session } = useAuth()
  const token = session?.access_token || ''
  const navigate = useNavigate()

  const [attempt, setAttempt] = useState<AttemptContent | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  // Assessment State
  const [currentIndex, setCurrentIndex] = useState(0)
  // Local answers map: question_id -> { selected_option_ids: string[], is_marked_for_review: boolean }
  const [answersMap, setAnswersMap] = useState<
    Record<string, { selected_option_ids: string[]; is_marked_for_review: boolean }>
  >({})

  // Autosave Status: 'saved' | 'saving' | 'error'
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error'>('saved')
  const [saveError, setSaveError] = useState<string | null>(null)

  // Timer countdown
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showSubmitModal, setShowSubmitModal] = useState(false)

  // Proctoring & Telemetry State
  const [violationCount, setViolationCount] = useState<number>(0)
  const [proctoringDeduction, setProctoringDeduction] = useState<number>(0)
  const [isFullscreen, setIsFullscreen] = useState<boolean>(true)
  const [showPolicyModal, setShowPolicyModal] = useState<boolean>(false)
  const [telemetryWarning, setTelemetryWarning] = useState<string | null>(null)
  const lastEventTimeMap = useRef<Record<string, number>>({})

  // Debounce autosave ref
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const handleFinalSubmitRef = useRef<(isAutoExpire?: boolean) => void>(() => {})

  // Load Attempt Content
  const loadContent = useCallback(async () => {
    if (!token || !attemptId) return
    setIsLoading(true)
    setLoadError(null)
    try {
      const data = await fetchAttemptContent(token, attemptId)
      setAttempt(data)
      setRemainingSeconds(data.remaining_seconds)
      setViolationCount(data.violation_count ?? 0)
      setProctoringDeduction(Number(data.proctoring_deduction ?? 0))

      // Initialize answers from server saved state
      const initialMap: Record<
        string,
        { selected_option_ids: string[]; is_marked_for_review: boolean }
      > = {}
      data.questions.forEach((q) => {
        initialMap[q.id] = {
          selected_option_ids: q.saved_answer ? [...q.saved_answer.selected_option_ids] : [],
          is_marked_for_review: q.saved_answer ? q.saved_answer.is_marked_for_review : false,
        }
      })
      setAnswersMap(initialMap)

      // If already finalized on server (e.g. expired)
      if (data.is_finalized) {
        navigate(`/student/assessments/${attemptId}/completed`, { replace: true })
      }
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load assessment.')
    } finally {
      setIsLoading(false)
    }
  }, [token, attemptId, navigate])

  useEffect(() => {
    loadContent()
  }, [loadContent])

  // Countdown Timer
  useEffect(() => {
    if (remainingSeconds <= 0) return

    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(interval)
          // Auto-submit when time expires
          handleFinalSubmitRef.current(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [remainingSeconds])

  // Proctoring Incident Reporter with Idempotency and Rate Limiting
  const reportProctoringEvent = useCallback(
    async (eventType: string, eventData: Record<string, any> = {}) => {
      if (!token || !attemptId || !attempt || attempt.is_finalized) return

      const now = Date.now()
      const lastTime = lastEventTimeMap.current[eventType] || 0
      // Rate-limit same event type to at most once per 1.5 seconds
      if (now - lastTime < 1500) return
      lastEventTimeMap.current[eventType] = now

      const clientEventId =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `evt_${now}_${Math.random().toString(36).substring(2, 9)}`

      try {
        const res = await sendTelemetry(token, attemptId, {
          event_type: eventType,
          client_event_id: clientEventId,
          event_data: { ...eventData, client_timestamp: new Date().toISOString() },
        })
        if (res.violation_count !== undefined) {
          setViolationCount(res.violation_count)
        }
        if (res.proctoring_deduction !== undefined) {
          setProctoringDeduction(Number(res.proctoring_deduction))
        }
        if (res.message && attempt.enable_proctoring_warnings !== false) {
          setTelemetryWarning(res.message)
        } else if (res.limit_exceeded && attempt.enable_proctoring_warnings !== false) {
          setTelemetryWarning(
            `Violation threshold reached (${res.violation_count} accepted violations). Proctoring deductions may apply.`
          )
        }
      } catch {
        // Non-blocking telemetry
      }
    },
    [token, attemptId, attempt]
  )

  // Fullscreen Enforcement Listener
  useEffect(() => {
    if (!attempt?.require_fullscreen) return

    const checkFullscreen = () => {
      const active = !!document.fullscreenElement
      setIsFullscreen(active)
      if (!active) {
        reportProctoringEvent('fullscreen_exit')
      }
    }

    setIsFullscreen(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', checkFullscreen)
    return () => {
      document.removeEventListener('fullscreenchange', checkFullscreen)
    }
  }, [attempt?.require_fullscreen, reportProctoringEvent])

  // Copy/Paste & Context Menu Prevention (Scoped to active assessment)
  useEffect(() => {
    if (!attempt?.enable_copy_paste_restriction) return

    const handleCopyCutPaste = (e: ClipboardEvent) => {
      e.preventDefault()
      if (attempt.enable_proctoring_warnings !== false) {
        setTelemetryWarning('Copy, cut, and paste actions are restricted during this assessment.')
      }
      reportProctoringEvent('copy_paste_attempt', { action: e.type })
    }

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault()
      if (attempt.enable_proctoring_warnings !== false) {
        setTelemetryWarning('Context menu is disabled during this assessment.')
      }
      reportProctoringEvent('copy_paste_attempt', { action: 'contextmenu' })
    }

    window.addEventListener('copy', handleCopyCutPaste)
    window.addEventListener('cut', handleCopyCutPaste)
    window.addEventListener('paste', handleCopyCutPaste)
    window.addEventListener('contextmenu', handleContextMenu)

    return () => {
      window.removeEventListener('copy', handleCopyCutPaste)
      window.removeEventListener('cut', handleCopyCutPaste)
      window.removeEventListener('paste', handleCopyCutPaste)
      window.removeEventListener('contextmenu', handleContextMenu)
    }
  }, [attempt?.enable_copy_paste_restriction, attempt?.enable_proctoring_warnings, reportProctoringEvent])

  // Developer Tools Shortcuts Intercept (F12, Ctrl/Cmd+Shift+I/J/C, Ctrl/Cmd+U)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isDevTools =
        e.key === 'F12' ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && ['I', 'i', 'J', 'j', 'C', 'c'].includes(e.key)) ||
        ((e.ctrlKey || e.metaKey) && (e.key === 'u' || e.key === 'U'))

      if (isDevTools) {
        e.preventDefault()
        if (attempt?.enable_proctoring_warnings !== false) {
          setTelemetryWarning('Developer tools shortcuts are disabled during this assessment.')
        }
        reportProctoringEvent('dev_tools_shortcut', { key: e.key })
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [attempt?.enable_proctoring_warnings, reportProctoringEvent])

  // Tab Switching & Window Blur Listeners
  useEffect(() => {
    if (!token || !attemptId || !attempt || attempt.is_finalized) return

    const onVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        reportProctoringEvent('tab_switch')
      }
    }

    const onBlur = () => {
      reportProctoringEvent('window_blur')
    }

    document.addEventListener('visibilitychange', onVisibilityChange)
    window.addEventListener('blur', onBlur)

    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange)
      window.removeEventListener('blur', onBlur)
    }
  }, [token, attemptId, attempt, reportProctoringEvent])

  // Immediate or Debounced Save
  const performSave = useCallback(
    async (
      questionId: string,
      selectedOptionIds: string[],
      isMarkedForReview: boolean
    ) => {
      if (!token || !attemptId) return
      setSaveStatus('saving')
      setSaveError(null)
      try {
        await autosaveAnswer(token, attemptId, questionId, {
          selected_option_ids: selectedOptionIds,
          is_marked_for_review: isMarkedForReview,
          client_timestamp: new Date().toISOString(),
        })
        setSaveStatus('saved')
      } catch (err) {
        setSaveStatus('error')
        setSaveError(err instanceof Error ? err.message : 'Autosave failed.')
      }
    },
    [token, attemptId]
  )

  const handleOptionChange = (questionId: string, optionId: string, qType: string) => {
    const current = answersMap[questionId] || {
      selected_option_ids: [],
      is_marked_for_review: false,
    }

    let newSelected: string[]
    if (qType === 'multiple_choice') {
      if (current.selected_option_ids.includes(optionId)) {
        newSelected = current.selected_option_ids.filter((id) => id !== optionId)
      } else {
        newSelected = [...current.selected_option_ids, optionId]
      }
    } else {
      // Single choice or True/False
      newSelected = [optionId]
    }

    const updated = {
      ...current,
      selected_option_ids: newSelected,
    }

    setAnswersMap((prev) => ({
      ...prev,
      [questionId]: updated,
    }))

    // Debounced save (800ms)
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current)
    saveTimeoutRef.current = setTimeout(() => {
      performSave(questionId, updated.selected_option_ids, updated.is_marked_for_review)
    }, 800)
  }

  const handleToggleReview = (questionId: string) => {
    const current = answersMap[questionId] || {
      selected_option_ids: [],
      is_marked_for_review: false,
    }
    const updated = {
      ...current,
      is_marked_for_review: !current.is_marked_for_review,
    }

    setAnswersMap((prev) => ({
      ...prev,
      [questionId]: updated,
    }))

    // Immediate save for review status
    performSave(questionId, updated.selected_option_ids, updated.is_marked_for_review)
  }

  // Navigation handlers
  const handleNavigate = (newIdx: number) => {
    if (!attempt) return
    if (newIdx < 0 || newIdx >= attempt.questions.length) return

    // If backtracking not allowed and trying to go back
    if (!attempt.allow_backtracking && newIdx < currentIndex) {
      return
    }

    // Flush any pending save for current question
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    const currentQ = attempt.questions[currentIndex]
    if (currentQ && answersMap[currentQ.id]) {
      const curr = answersMap[currentQ.id]
      performSave(currentQ.id, curr.selected_option_ids, curr.is_marked_for_review)
    }

    setCurrentIndex(newIdx)
  }

  // Final Submit Handler
  const handleFinalSubmit = async (isAutoExpire = false) => {
    if (!token || !attemptId || isSubmitting) return
    setIsSubmitting(true)
    setShowSubmitModal(false)

    try {
      // Flush current answer if pending
      if (attempt) {
        const currentQ = attempt.questions[currentIndex]
        if (currentQ && answersMap[currentQ.id]) {
          const curr = answersMap[currentQ.id]
          await autosaveAnswer(token, attemptId, currentQ.id, {
            selected_option_ids: curr.selected_option_ids,
            is_marked_for_review: curr.is_marked_for_review,
            client_timestamp: new Date().toISOString(),
          }).catch(() => null)
        }
      }

      await submitAttempt(token, attemptId)
      navigate(`/student/assessments/${attemptId}/completed`, {
        replace: true,
        state: { autoExpired: isAutoExpire },
      })
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Submission failed.')
      setIsSubmitting(false)
    }
  }

  useEffect(() => {
    handleFinalSubmitRef.current = handleFinalSubmit
  })

  // Format Timer HH:MM:SS
  const formatTimer = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (hrs > 0) {
      return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mb-3" />
        <h2 className="text-sm font-semibold text-slate-800">Loading Assessment Environment...</h2>
        <p className="text-xs text-slate-500 mt-1">Establishing secure session & timer sync</p>
      </div>
    )
  }

  if (loadError || !attempt) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 bg-white border border-red-200 rounded-xl shadow-sm text-center">
        <AlertOctagon className="w-12 h-12 text-red-500 mx-auto mb-3" />
        <h2 className="text-base font-bold text-slate-900">Assessment Error</h2>
        <p className="text-xs text-slate-600 mt-2">{loadError || 'Assessment could not be loaded.'}</p>
        <button
          onClick={() => navigate('/student/portal')}
          className="mt-6 px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-lg transition-colors"
        >
          Return to Portal
        </button>
      </div>
    )
  }

  const currentQ: SanitizedQuestion = attempt.questions[currentIndex]
  const currentAnswer = answersMap[currentQ?.id] || {
    selected_option_ids: [],
    is_marked_for_review: false,
  }

  // Summary counts for palette and modal
  let answeredCount = 0
  let reviewCount = 0
  attempt.questions.forEach((q) => {
    const ans = answersMap[q.id]
    if (ans && ans.selected_option_ids.length > 0) answeredCount++
    if (ans && ans.is_marked_for_review) reviewCount++
  })
  const unansweredCount = attempt.questions.length - answeredCount

  const isTimerUrgent = remainingSeconds < 180 // under 3 mins
  const isTimerWarning = remainingSeconds < 600 // under 10 mins

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col text-slate-900 select-none">
      {/* Top Banner Header */}
      <header className="bg-slate-900 text-white px-4 py-3 shadow-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-800 text-blue-400 border border-slate-700">
              {attempt.course_code}
            </span>
            <h1 className="text-sm font-bold text-slate-100 truncate max-w-xs sm:max-w-md">
              {attempt.quiz_title}
            </h1>
          </div>

          <div className="flex items-center space-x-4">
            {/* Autosave Indicator */}
            <div className="hidden sm:flex items-center space-x-1.5 text-xs">
              {saveStatus === 'saving' && (
                <span className="text-slate-400 flex items-center space-x-1">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
                  <span>Saving...</span>
                </span>
              )}
              {saveStatus === 'saved' && (
                <span className="text-emerald-400 flex items-center space-x-1 font-medium">
                  <Check className="w-3.5 h-3.5" />
                  <span>All answers saved</span>
                </span>
              )}
              {saveStatus === 'error' && (
                <span className="text-amber-400 flex items-center space-x-1 font-medium" title={saveError || ''}>
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Save failed (retrying)</span>
                </span>
              )}
            </div>

            {/* Countdown Clock */}
            <div
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-mono font-bold border transition-colors ${
                isTimerUrgent
                  ? 'bg-red-600 text-white border-red-500 animate-pulse'
                  : isTimerWarning
                  ? 'bg-amber-600 text-white border-amber-500'
                  : 'bg-slate-800 text-slate-200 border-slate-700'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>{formatTimer(remainingSeconds)}</span>
            </div>

            {/* Live Proctoring Status Indicator */}
            <button
              type="button"
              onClick={() => setShowPolicyModal(true)}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border transition-colors ${
                violationCount > (attempt.tab_switch_limit ?? 2)
                  ? 'bg-red-950/80 border-red-500/60 text-red-300 hover:bg-red-900/80'
                  : violationCount > 0
                  ? 'bg-amber-950/80 border-amber-500/60 text-amber-300 hover:bg-amber-900/80'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-750'
              }`}
              title="Click to view proctoring policy and live violation details"
            >
              <Shield
                className={`w-3.5 h-3.5 ${
                  violationCount > (attempt.tab_switch_limit ?? 2)
                    ? 'text-red-400'
                    : violationCount > 0
                    ? 'text-amber-400'
                    : 'text-emerald-400'
                }`}
              />
              <span className="hidden sm:inline">Violations:</span>
              <span>{violationCount}</span>
              {proctoringDeduction > 0 && (
                <span className="font-mono text-red-400 font-bold ml-0.5">
                  (-{proctoringDeduction.toFixed(2)})
                </span>
              )}
            </button>

            {/* Submit Trigger */}
            <button
              onClick={() => setShowSubmitModal(true)}
              disabled={isSubmitting}
              className="px-3.5 py-1 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors shadow-sm disabled:opacity-50 flex items-center space-x-1.5"
            >
              <Send className="w-3 h-3" />
              <span>Submit</span>
            </button>
          </div>
        </div>
      </header>

      {/* Fullscreen Required Alert Banner */}
      {attempt.require_fullscreen && !isFullscreen && (
        <div className="bg-red-600 text-white px-4 py-2.5 text-xs font-semibold flex items-center justify-between shadow-inner">
          <div className="flex items-center space-x-2">
            <AlertOctagon className="w-4 h-4 shrink-0 animate-bounce" />
            <span>
              <strong>Fullscreen Exited:</strong> Fullscreen mode is mandatory for this assessment. Fullscreen exits are monitored and logged.
            </span>
          </div>
          <button
            type="button"
            onClick={async () => {
              try {
                if (document.documentElement.requestFullscreen) {
                  await document.documentElement.requestFullscreen()
                  setIsFullscreen(true)
                }
              } catch {
                // browser blocked or unsupported
              }
            }}
            className="px-3 py-1 bg-white text-red-700 hover:bg-red-50 rounded font-bold text-xs shadow-sm transition-colors cursor-pointer"
          >
            Return to Fullscreen
          </button>
        </div>
      )}

      {/* Telemetry Alert Banner */}
      {telemetryWarning && (
        <div className="bg-amber-500 text-slate-950 px-4 py-2 text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{telemetryWarning}</span>
          </div>
          <button
            onClick={() => setTelemetryWarning(null)}
            className="text-[11px] underline hover:opacity-80 ml-4 font-bold"
          >
            Acknowledge
          </button>
        </div>
      )}

      {/* Main Assessment Body */}
      <div className="max-w-7xl mx-auto w-full flex-1 p-4 grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Left: Question Pane */}
        <div className="lg:col-span-3 flex flex-col justify-between bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div>
            {/* Question Header & Meta */}
            <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                  Question {currentIndex + 1} of {attempt.questions.length}
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-600">
                  {currentQ.question_type === 'single_choice'
                    ? 'Single Choice'
                    : currentQ.question_type === 'multiple_choice'
                    ? 'Multiple Choice'
                    : 'True / False'}
                </span>
              </div>

              <div className="flex items-center space-x-3 text-xs">
                <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                  +{currentQ.positive_marks} Marks
                </span>
                {currentQ.negative_marks > 0 && (
                  <span className="font-semibold text-red-700 bg-red-50 px-2 py-0.5 rounded">
                    -{currentQ.negative_marks} Neg
                  </span>
                )}
              </div>
            </div>

            {/* Prompt */}
            <div className="py-6">
              <p className="text-base text-slate-900 leading-relaxed font-medium whitespace-pre-line">
                {currentQ.prompt}
              </p>
            </div>

            {/* Options Selector */}
            <div className="space-y-3 pt-2">
              {currentQ.options.map((opt, oIdx) => {
                const isSelected = currentAnswer.selected_option_ids.includes(opt.id)
                const isMultiple = currentQ.question_type === 'multiple_choice'
                const optionLetter = String.fromCharCode(65 + oIdx) // A, B, C, D

                return (
                  <div
                    key={opt.id}
                    onClick={() => handleOptionChange(currentQ.id, opt.id, currentQ.question_type)}
                    className={`flex items-start p-3.5 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-blue-50/80 border-blue-500 ring-1 ring-blue-500 shadow-sm'
                        : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                    }`}
                  >
                    <div className="flex items-center h-5 mr-3">
                      <input
                        type={isMultiple ? 'checkbox' : 'radio'}
                        name={`question_${currentQ.id}`}
                        checked={isSelected}
                        onChange={() => {}} // handled by parent div
                        className={`w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500 ${
                          !isMultiple ? 'rounded-full' : ''
                        }`}
                      />
                    </div>
                    <div className="flex items-start space-x-2 flex-1">
                      <span className="text-xs font-bold text-slate-500">{optionLetter}.</span>
                      <span className="text-sm text-slate-800 leading-snug">{opt.option_text}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Question Footer Toolbar */}
          <div className="mt-8 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <button
              onClick={() => handleToggleReview(currentQ.id)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                currentAnswer.is_marked_for_review
                  ? 'bg-amber-100 text-amber-900 border-amber-300'
                  : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
              }`}
            >
              <Flag
                className={`w-3.5 h-3.5 ${
                  currentAnswer.is_marked_for_review ? 'fill-amber-600 text-amber-600' : ''
                }`}
              />
              <span>
                {currentAnswer.is_marked_for_review ? 'Marked for Review' : 'Mark for Review'}
              </span>
            </button>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleNavigate(currentIndex - 1)}
                disabled={currentIndex === 0 || !attempt.allow_backtracking}
                className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <button
                onClick={() => handleNavigate(currentIndex + 1)}
                disabled={currentIndex === attempt.questions.length - 1}
                className="flex items-center space-x-1 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
              >
                <span>Next</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Right: Palette & Summary Sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide mb-3">
              Question Navigator
            </h3>

            {/* Grid of question buttons */}
            <div className="grid grid-cols-5 gap-2">
              {attempt.questions.map((q, qIdx) => {
                const ans = answersMap[q.id]
                const isCurrent = qIdx === currentIndex
                const isAnswered = ans && ans.selected_option_ids.length > 0
                const isReview = ans && ans.is_marked_for_review

                let btnStyle = 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                if (isReview) {
                  btnStyle = 'bg-amber-100 text-amber-900 border-amber-300 font-bold'
                } else if (isAnswered) {
                  btnStyle = 'bg-emerald-600 text-white border-emerald-600 font-semibold'
                }

                if (isCurrent) {
                  btnStyle += ' ring-2 ring-blue-600 ring-offset-1'
                }

                const canClick = attempt.allow_backtracking || qIdx >= currentIndex

                return (
                  <button
                    key={q.id}
                    disabled={!canClick}
                    onClick={() => handleNavigate(qIdx)}
                    className={`h-9 w-full rounded-lg text-xs flex items-center justify-center border transition-all relative ${btnStyle} ${
                      !canClick ? 'opacity-40 cursor-not-allowed' : ''
                    }`}
                  >
                    <span>{qIdx + 1}</span>
                    {isReview && (
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-600 absolute top-1 right-1" />
                    )}
                  </button>
                )
              })}
            </div>

            {/* Legend */}
            <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 gap-2 text-[11px] text-slate-600">
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded bg-emerald-600 inline-block shrink-0" />
                <span>Answered ({answeredCount})</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded bg-white border border-slate-300 inline-block shrink-0" />
                <span>Unanswered ({unansweredCount})</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded bg-amber-100 border border-amber-300 inline-block shrink-0" />
                <span>Review ({reviewCount})</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded border-2 border-blue-600 inline-block shrink-0" />
                <span>Current</span>
              </div>
            </div>
          </div>

          {/* Assessment Integrity Notice */}
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-xs text-slate-600 space-y-1.5">
            <div className="font-semibold text-slate-800 flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-blue-600" />
              <span>Assessment Rules</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-500">
              Autosave records responses continuously in the background. Navigation across tabs or
              loss of window focus is monitored and logged as telemetry.
            </p>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full border border-slate-200 p-6 text-slate-900">
            <h3 className="text-base font-bold text-slate-900">Submit Assessment?</h3>
            <p className="text-xs text-slate-600 mt-1">
              Please review your completion status before finalizing your attempt.
            </p>

            <div className="my-5 p-4 bg-slate-50 border border-slate-200 rounded-lg grid grid-cols-3 gap-3 text-center">
              <div>
                <div className="text-lg font-bold text-emerald-600">{answeredCount}</div>
                <div className="text-[11px] text-slate-500">Answered</div>
              </div>
              <div>
                <div className="text-lg font-bold text-red-600">{unansweredCount}</div>
                <div className="text-[11px] text-slate-500">Unanswered</div>
              </div>
              <div>
                <div className="text-lg font-bold text-amber-600">{reviewCount}</div>
                <div className="text-[11px] text-slate-500">For Review</div>
              </div>
            </div>

            {unansweredCount > 0 && (
              <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span>
                  You have <span className="font-bold">{unansweredCount} unanswered</span> questions.
                  Unanswered questions receive zero marks.
                </span>
              </div>
            )}

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowSubmitModal(false)}
                className="px-4 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Continue Assessment
              </button>
              <button
                type="button"
                onClick={() => handleFinalSubmit(false)}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 flex items-center space-x-1.5"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Submitting...</span>
                  </>
                ) : (
                  <span>Confirm & Submit</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Proctoring Policy & Status Modal */}
      {showPolicyModal && attempt && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full border border-slate-200 p-6 text-slate-900">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Shield className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">Proctoring Policy & Live Status</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowPolicyModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="my-4 space-y-4 text-xs">
              {/* Summary Stats */}
              <div className="grid grid-cols-3 gap-2 text-center p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <div>
                  <div className="text-base font-bold text-slate-800">{violationCount}</div>
                  <div className="text-[11px] text-slate-500">Recorded Violations</div>
                </div>
                <div>
                  <div className="text-base font-bold text-blue-600">
                    {Math.max(0, (attempt.tab_switch_limit ?? 2) - violationCount)}
                  </div>
                  <div className="text-[11px] text-slate-500">Free Remaining</div>
                </div>
                <div>
                  <div className="text-base font-bold text-red-600">
                    -{proctoringDeduction.toFixed(2)}
                  </div>
                  <div className="text-[11px] text-slate-500">Current Deduction</div>
                </div>
              </div>

              {/* Rules Breakdown */}
              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                  Configured Assessment Rules
                </h4>
                <ul className="space-y-1.5 text-slate-600 list-disc list-inside">
                  <li>
                    <strong>Free Allowance:</strong> First {attempt.tab_switch_limit ?? 2} violations are free with 0 penalty deduction.
                  </li>
                  <li>
                    <strong>Deduction Rate:</strong> {Number(attempt.tab_switch_penalty_marks ?? attempt.tab_switch_penalty ?? 1).toFixed(2)} marks deducted per chargeable violation thereafter.
                  </li>
                  <li>
                    <strong>Maximum Deduction:</strong> Capped at {Number(attempt.max_proctoring_deduction ?? 5).toFixed(2)} marks total (deduction never exceeds your score).
                  </li>
                  <li>
                    <strong>Copy / Paste:</strong>{' '}
                    {attempt.enable_copy_paste_restriction
                      ? `Restricted (${attempt.count_copy_paste_violations ? 'counts as violation' : 'blocked only'})`
                      : 'Allowed'}
                  </li>
                  <li>
                    <strong>Fullscreen Requirement:</strong>{' '}
                    {attempt.require_fullscreen
                      ? `Required (${attempt.count_fullscreen_exit_violations ? 'exits count as violation' : 'monitored only'})`
                      : 'Optional'}
                  </li>
                  <li>
                    <strong>Tab / Focus Switching:</strong>{' '}
                    {attempt.count_tab_switch_violations ? 'Counts toward violation policy' : 'Monitored without score penalty'}
                  </li>
                  <li>
                    <strong>Developer Tools Shortcuts:</strong>{' '}
                    {attempt.count_dev_tools_violations ? 'Restricted (counts as violation)' : 'Monitored'}
                  </li>
                </ul>
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900 text-[11px] leading-relaxed">
                <strong>Transparent Scoring:</strong> Telemetry events are deduplicated and validated on the backend. Your score before deductions and the proctoring deduction are kept separate and auditable.
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowPolicyModal(false)}
                className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
