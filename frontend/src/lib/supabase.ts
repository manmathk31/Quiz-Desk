import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const rawUrl = import.meta.env.VITE_SUPABASE_URL || ''
const rawKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

/**
 * Validates whether real Supabase configuration values have been provided.
 * Rejects empty strings and default placeholder values from .env.example.
 */
export const isSupabaseConfigured = Boolean(
  rawUrl &&
    rawKey &&
    !rawUrl.includes('your-project.supabase.co') &&
    rawKey !== 'your-anon-key' &&
    rawKey.length > 20
)

if (!isSupabaseConfigured && import.meta.env.DEV) {
  console.warn(
    '[Quizdesk Auth] Supabase credentials not configured in frontend/.env.local. ' +
      'Authentication operations will remain unconfigured until live credentials are provided.'
  )
}

// Fallback URL and key so client initialization does not throw at runtime when unconfigured
const effectiveUrl = isSupabaseConfigured ? rawUrl : 'https://unconfigured.local.supabase.co'
const effectiveKey = isSupabaseConfigured ? rawKey : 'unconfigured-placeholder-anon-key'

export const supabase: SupabaseClient = createClient(effectiveUrl, effectiveKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})
