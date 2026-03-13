export const CAT_ERRORS: Record<string, string> = {
  network:  "Oops, claws got tangled 🙀 — can't reach the server",
  notFound: "This cat has wandered off 🐾 — not found",
  auth:     "You need to be a proper kitten to do that 😾",
  server:   "The cat knocked something off the shelf 💥 — server error",
  timeout:  "Catnap too long 💤 — request timed out",
  parse:    "Hairball in the data 🤢 — invalid response",
  unknown:  "Something went sideways 🐱 — try again",
}

export function catError(status?: number): string {
  if (!status) return CAT_ERRORS.network
  if (status === 404) return CAT_ERRORS.notFound
  if (status === 401 || status === 403) return CAT_ERRORS.auth
  if (status >= 500) return CAT_ERRORS.server
  return CAT_ERRORS.unknown
}
