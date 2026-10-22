import type { Session, User as SupabaseUser } from '@supabase/supabase-js'

export type UserRole = 'student' | 'teacher' | 'admin'

export interface UserProfile {
  id: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
}

export type ProfileStatus = 'idle' | 'loading' | 'resolved' | 'endpoint_unavailable' | 'error'

export interface AuthState {
  session: Session | null
  user: SupabaseUser | null
  profile: UserProfile | null
  role: UserRole | null
  loading: boolean
  isConfigured: boolean
  profileStatus: ProfileStatus
  profileError: string | null
}

export interface AuthContextValue extends AuthState {
  signInWithEmail: (email: string, password: string) => Promise<{ error: Error | null }>
  signOut: () => Promise<void>
  refreshProfile: () => Promise<void>
}
