import React, { useState } from 'react'
import { X, UserPlus, AlertCircle } from 'lucide-react'
import { addSingleAssignment } from '../../services/rosterApi'
import type { Assignment } from '../../types/roster'

interface AddStudentModalProps {
  isOpen: boolean
  onClose: () => void
  quizId: string
  token: string
  onStudentAdded: (student: Assignment) => void
}

export const AddStudentModal: React.FC<AddStudentModalProps> = ({
  isOpen,
  onClose,
  quizId,
  token,
  onStudentAdded,
}) => {
  const [prn, setPrn] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [division, setDivision] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prn.trim() || !name.trim() || !email.trim() || !division.trim()) {
      setError('All fields are required.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const added = await addSingleAssignment(token, quizId, {
        prn: prn.trim(),
        name: name.trim(),
        email: email.trim().toLowerCase(),
        division: division.trim().toUpperCase(),
      })
      onStudentAdded(added)
      // Reset form and close
      setPrn('')
      setName('')
      setEmail('')
      setDivision('')
      onClose()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to add student.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-slate-800">Add Student Assignment</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2.5 text-sm text-rose-700">
              <AlertCircle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Permanent Registration Number (PRN) *
            </label>
            <input
              type="text"
              required
              value={prn}
              onChange={(e) => setPrn(e.target.value)}
              placeholder="e.g. 202401110001 or 00123"
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
            <p className="text-xs text-slate-500 mt-1">Leading zeros will be strictly preserved.</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Student Full Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Aarav Sharma"
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Institutional Email *
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. aarav.sharma@college.edu"
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Class Division / Batch *
            </label>
            <input
              type="text"
              required
              value={division}
              onChange={(e) => setDivision(e.target.value)}
              placeholder="e.g. A, CS-1, or Batch-B"
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Assigning...' : 'Assign Student'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
