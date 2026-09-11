export type SiteIdentityEnv = { SITE_IDENTITY_ALIASES?: string }

// Only use identity headers supplied by the Sites dispatcher. Some older
// sessions currently forward email without the stable Site user ID. An
// operator-verified, server-only alias restores that same existing owner key;
// never infer ownership from a request body, the first DB row or a new email.
export function siteOwner(request: Request, env: SiteIdentityEnv): string | null {
  const id = request.headers.get('oai-authenticated-user-id')?.trim()
  if (id) return id
  const email = request.headers.get('oai-authenticated-user-email')?.trim().toLowerCase()
  if (!email || !env.SITE_IDENTITY_ALIASES) return null
  try {
    const aliases: unknown = JSON.parse(env.SITE_IDENTITY_ALIASES)
    if (!aliases || typeof aliases !== 'object' || Array.isArray(aliases) || !Object.hasOwn(aliases, email)) return null
    const owner = (aliases as Record<string, unknown>)[email]
    return typeof owner === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(owner) ? owner : null
  } catch { return null }
}
