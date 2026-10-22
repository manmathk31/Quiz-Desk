import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
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

  /**
   * Resolve user profile and authoritative role from trusted backend API.
   * As specified in DEC-001, DEC-013, and DEC-015:
   * Roles are NEVER inferred from client-editable Supabase user metadata.
   * If the backend profile endpoint is pending, role remains null (unknown).
   */
  const resolveBackendProfile = useCallback(
    async (accessToken: string) => {
      setProfileStatus('loading')
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          const data: UserProfile = await response.json()
          setProfile(data)
          setRole(data.role)
          setProfileStatus('resolved')
          setProfileError(null)
          return
        }

        if (response.status === 404) {
          // Backend profile endpoint has not been implemented yet
          setProfile(null)
          setRole(null)
          setProfileStatus('endpoint_unavailable')
          setProfileError(
            'Backend profile endpoint (/api/v1/users/me) pending implementation. Authoritative role is unknown.'
          )
          return
        }

        // Other HTTP error (e.g. 401 token rejected, 403 inactive account)
        setProfile(null)
        setRole(null)
        setProfileStatus('error')
        setProfileError(`Backend authentication error: HTTP ${response.status}`)
      } catch {
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
    let isMounted = true

    if (!isSupabaseConfigured) {
      if (isMounted) {
        setLoading(false)
        setProfileStatus('idle')
      }
      return
    }

    // 1. Initial session hydration
    supabase.auth
      .getSession()
      .then(async ({ data: { session: initialSession }, error }) => {
        if (!isMounted) return

        if (error) {
          console.error('[Quizdesk Auth] Error fetching initial session:', error.message)
          setSession(null)
          setUser(null)
          setLoading(false)
          return
        }

        setSession(initialSession)
        setUser(initialSession?.user ?? null)

        if (initialSession?.access_token) {
          await resolveBackendProfile(initialSession.access_token)
        } else {
          setProfile(null)
          setRole(null)
          setProfileStatus('idle')
          setProfileError(null)
        }

        if (isMounted) {
          setLoading(false)
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error('[Quizdesk Auth] Unexpected error initializing session:', err)
          setLoading(false)
        }
      })

    // 2. Realtime auth state change subscription
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, newSession) => {
      if (!isMounted) return

      setSession(newSession)
      setUser(newSession?.user ?? null)

      if (newSession?.access_token) {
        await resolveBackendProfile(newSession.access_token)
      } else {
        setProfile(null)
        setRole(null)
        setProfileStatus('idle')
        setProfileError(null)
      }

      if (isMounted) {
        setLoading(false)
      }
    })

    return () => {
      isMounted = false
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
