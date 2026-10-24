import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useRef,
  type PropsWithChildren,
} from 'react'
import type { Session, User as SupabaseUser } from '@supabase/supabase-js'
import { supabase, isSupabaseConfigured } from '../lib/supabase'
import type {
  UserRole,
  UserProfile,
  ProfileStatus,
  AuthContextValue,
} from '../types/auth'

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const AuthProvider: React.FC<PropsWithChildren> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<SupabaseUser | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [role, setRole] = useState<UserRole | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [profileStatus, setProfileStatus] = useState<ProfileStatus>('idle')
  const [profileError, setProfileError] = useState<string | null>(null)

  // Track active token and mounted state to discard stale in-flight requests and prevent race conditions
  const activeTokenRef = useRef<string | null>(null)
  const isMountedRef = useRef<boolean>(true)

  /**
   * Resolve user profile and authoritative role from trusted backend API.
   * As specified in DEC-001, DEC-013, and DEC-015:
   * Roles are NEVER inferred from client-editable Supabase user metadata.
   * If the backend profile endpoint fails or is pending, role remains null (unknown).
   */
  const resolveBackendProfile = useCallback(
    async (accessToken: string) => {
      activeTokenRef.current = accessToken
      setProfileStatus('loading')
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        })

        // Guard against race conditions: if user signed out or token changed while fetch was in-flight
        if (!isMountedRef.current || activeTokenRef.current !== accessToken) {
          return
        }

        if (response.ok) {
          const data: UserProfile = await response.json()
          setProfile(data)
          setRole(data.role)
          setProfileStatus('resolved')
          setProfileError(null)
          return
        }

        let detailMsg: string | null = null
        try {
          const errData = await response.json()
          if (errData?.detail && typeof errData.detail === 'string') {
            detailMsg = errData.detail
          }
        } catch {
          // ignore parsing error if response has no JSON body
        }

        // Token rejected, account deactivated, or unregistered user: strictly clear profile & role
        if (response.status === 401) {
          setProfile(null)
          setRole(null)
          setProfileStatus('error')
          setProfileError(
            detailMsg
              ? `${detailMsg} (HTTP 401)`
              : 'User not registered in database or session expired (HTTP 401).'
          )
          return
        }

        if (response.status === 403) {
          setProfile(null)
          setRole(null)
          setProfileStatus('error')
          setProfileError('Access restricted: Account deactivated or unapproved (HTTP 403).')
          return
        }

        if (response.status === 404) {
          setProfile(null)
          setRole(null)
          setProfileStatus('endpoint_unavailable')
          setProfileError(
            'Backend profile endpoint (/api/v1/users/me) pending implementation. Authoritative role is unknown.'
          )
          return
        }

        // Other HTTP error
        setProfile(null)
        setRole(null)
        setProfileStatus('error')
        setProfileError(`Backend authentication error: HTTP ${response.status}`)
      } catch {
        if (!isMountedRef.current || activeTokenRef.current !== accessToken) {
          return
        }
        // Network or connection error (e.g. backend server offline)
        setProfile(null)
        setRole(null)
        setProfileStatus('endpoint_unavailable')
        setProfileError(
          'Backend service unreachable. Authoritative application role cannot be confirmed.'
        )
      }
    },
    []
  )

  useEffect(() => {
    isMountedRef.current = true

    if (!isSupabaseConfigured) {
      if (isMountedRef.current) {
        setLoading(false)
        setProfileStatus('idle')
      }
      return
    }

    // 1. Initial session hydration
    supabase.auth
      .getSession()
      .then(async ({ data: { session: initialSession }, error }) => {
        if (!isMountedRef.current) return

        if (error) {
          console.error('[Quizdesk Auth] Error fetching initial session:', error.message)
          activeTokenRef.current = null
          setSession(null)
          setUser(null)
          setProfile(null)
          setRole(null)
          setProfileStatus('idle')
          setProfileError(null)
          setLoading(false)
          return
        }

        setSession(initialSession)
        setUser(initialSession?.user ?? null)

        if (initialSession?.access_token) {
          await resolveBackendProfile(initialSession.access_token)
        } else {
          activeTokenRef.current = null
          setProfile(null)
          setRole(null)
          setProfileStatus('idle')
          setProfileError(null)
        }

        if (isMountedRef.current) {
          setLoading(false)
        }
      })
      .catch((err) => {
        if (isMountedRef.current) {
          console.error('[Quizdesk Auth] Unexpected error initializing session:', err)
          setLoading(false)
        }
      })

    // 2. Realtime auth state change subscription
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, newSession) => {
      if (!isMountedRef.current) return

      if (event === 'SIGNED_OUT' || !newSession) {
        activeTokenRef.current = null
        setSession(null)
        setUser(null)
        setProfile(null)
        setRole(null)
        setProfileStatus('idle')
        setProfileError(null)
        setLoading(false)
        return
      }

      setSession(newSession)
      setUser(newSession.user ?? null)

      if (newSession.access_token) {
        await resolveBackendProfile(newSession.access_token)
      } else {
        activeTokenRef.current = null
        setProfile(null)
        setRole(null)
        setProfileStatus('idle')
        setProfileError(null)
      }

      if (isMountedRef.current) {
        setLoading(false)
      }
    })

    return () => {
      isMountedRef.current = false
      subscription.unsubscribe()
    }
  }, [resolveBackendProfile])

  const signInWithEmail = useCallback(async (email: string, password: string) => {
    if (!isSupabaseConfigured) {
      return {
        error: new Error(
          'Supabase is not configured. Please supply VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.'
        ),
      }
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    return { error }
  }, [])

  const signOut = useCallback(async () => {
    activeTokenRef.current = null
    if (isSupabaseConfigured) {
      await supabase.auth.signOut()
    }
    setSession(null)
    setUser(null)
    setProfile(null)
    setRole(null)
    setProfileStatus('idle')
    setProfileError(null)
  }, [])

  const refreshProfile = useCallback(async () => {
    if (session?.access_token) {
      await resolveBackendProfile(session.access_token)
    }
  }, [session, resolveBackendProfile])


  const value: AuthContextValue = {
    session,
    user,
    profile,
    role,
    loading,
    isConfigured: isSupabaseConfigured,
    profileStatus,
    profileError,
    signInWithEmail,
    signOut,
    refreshProfile,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
