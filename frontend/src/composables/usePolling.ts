// Periodic background refetch for views whose data changes under the user
// (another TA grading the same session, an admin flipping a session open).
import {
  computed,
  onMounted,
  onUnmounted,
  ref,
  toValue,
  watch,
  type ComputedRef,
  type MaybeRefOrGetter,
  type Ref,
} from 'vue'
import { isAxiosError } from 'axios'
import { useAuthStore } from '../store/auth'

// 30s is the default: a lab session is graded by a handful of TAs at once, so
// seeing another TA's evaluation within half a minute is timely, while an open
// tab costs only ~2 Cloud Run requests per minute (and none while hidden).
export const POLL_INTERVAL_MS = 30_000

// Per-tick deadline. The axios instance sets no timeout, so without this one
// stalled request would keep `inFlight` true forever and every later tick
// would skip — polling would die silently.
export const POLL_TIMEOUT_MS = 15_000

// Consecutive failures stretch the interval up to this multiple, so a backend
// that is down is not hammered by every open tab.
const MAX_BACKOFF_FACTOR = 8

// How often the "Updated Ns ago" label recomputes. Coarser than 1s on
// purpose: the label is rounded to 10s, so it changes at most once per tick
// of this clock and never flickers.
const CLOCK_INTERVAL_MS = 10_000

/**
 * Handed to `refetch` so a tick can tell whether its result is still wanted.
 *
 * `isStale()` is the stale-overwrite guard: a load function must check it
 * *after* awaiting its requests and *before* assigning to component state.
 * It turns true when the component unmounted, when polling stopped, or when
 * a mutation handler called `invalidate()` while the tick was in flight —
 * exactly the case where the tick is holding a pre-mutation snapshot that
 * would revert what the user just did.
 */
export interface PollContext {
  // Aborts on unmount, on logout, on `invalidate()` and on the per-tick
  // deadline. Forward it to the API calls so the request is really dropped.
  signal: AbortSignal
  isStale: () => boolean
}

export interface PollingOptions {
  intervalMs?: number
  timeoutMs?: number
  // Truthy whenever the view must not be refetched under the user: an open
  // modal, an inline edit row, a half-filled create form.
  paused?: MaybeRefOrGetter<boolean>
}

export interface Polling {
  // Suspend/resume from an imperative handler, for state a `paused` getter
  // cannot see (an open combobox dropdown, say). Nestable: resume() only
  // lifts the suspension once every pause() has been matched.
  pause: () => void
  resume: () => void
  // Called by every mutation handler: discards the result of any tick still
  // in flight, so a pre-mutation snapshot can never land on top of the local
  // state the handler just updated.
  invalidate: () => void
  // Attempt time of the last tick (success or failure), for the staleness
  // indicator. `null` until the first tick runs.
  lastRunAt: Ref<number | null>
  // True once polling has given up for good (a 401 — the axios interceptor
  // is redirecting to /login).
  stopped: Ref<boolean>
  // Small human label for the header: "Updated 40s ago" / "Live updates
  // paused". Lets a user tell live data from arbitrarily stale data.
  statusText: ComputedRef<string>
}

/**
 * Calls `refetch` every `intervalMs` while the component is mounted, the tab
 * is visible, the user is logged in and nothing has suspended polling. Errors
 * from a tick are swallowed so a failed background refresh never replaces the
 * data or the error state the user is looking at; `refetch` should therefore
 * update state quietly (no loading flag) and must honour `ctx.isStale()`.
 */
export function usePolling(
  refetch: (ctx: PollContext) => Promise<void>,
  options: PollingOptions = {},
): Polling {
  const { intervalMs = POLL_INTERVAL_MS, timeoutMs = POLL_TIMEOUT_MS, paused } = options
  const auth = useAuthStore()

  let timer: number | null = null
  let deadline: number | null = null
  let clock: number | null = null
  let controller: AbortController | null = null
  let inFlight = false
  let failures = 0
  let mounted = false
  // Bumped by invalidate(); a tick whose captured value no longer matches is
  // holding stale data.
  let generation = 0

  const stopped = ref(false)
  const manualPauses = ref(0)
  const lastRunAt = ref<number | null>(null)
  const now = ref(Date.now())

  function clearTimer() {
    if (timer !== null) {
      window.clearTimeout(timer)
      timer = null
    }
  }

  function clearDeadline() {
    if (deadline !== null) {
      window.clearTimeout(deadline)
      deadline = null
    }
  }

  function suspended(): boolean {
    return (
      stopped.value ||
      manualPauses.value > 0 ||
      !auth.token ||
      toValue(paused) === true
    )
  }

  // Chained setTimeout rather than setInterval: a slow response can never pile
  // up ticks, because the next one is scheduled only after this one settles.
  function schedule() {
    clearTimer()
    if (stopped.value || !mounted || document.visibilityState === 'hidden') return
    const factor = Math.min(2 ** failures, MAX_BACKOFF_FACTOR)
    timer = window.setTimeout(tick, intervalMs * factor)
  }

  async function tick() {
    timer = null
    // Skip (never queue) the tick while a refetch is still in flight or the
    // user is mid-interaction.
    if (!suspended() && !inFlight) await run()
    schedule()
  }

  async function run() {
    const generationAtStart = generation
    const ticketController = new AbortController()
    controller = ticketController
    inFlight = true
    const ctx: PollContext = {
      signal: ticketController.signal,
      isStale: () => generationAtStart !== generation || stopped.value || !mounted,
    }
    clearDeadline()
    deadline = window.setTimeout(() => ticketController.abort(), timeoutMs)
    try {
      await refetch(ctx)
      failures = 0
    } catch (e: unknown) {
      failures += 1
      // Silent: keep the current data and retry (with backoff) on the next
      // tick. A 401 is the exception — the axios interceptor is already
      // redirecting to /login, so stop instead of firing during the redirect.
      if (isAxiosError(e) && e.response?.status === 401) stopped.value = true
    } finally {
      clearDeadline()
      if (controller === ticketController) controller = null
      inFlight = false
      // Attempt time, not success time: otherwise every tab re-focus fires an
      // extra immediate request for as long as the backend keeps failing.
      lastRunAt.value = Date.now()
      now.value = lastRunAt.value
    }
  }

  // Polling a backgrounded tab burns requests for nothing; on return, refetch
  // straight away if the data went stale while the tab was hidden.
  async function onVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      clearTimer()
      return
    }
    now.value = Date.now()
    const at = lastRunAt.value
    if (!suspended() && !inFlight && (at === null || Date.now() - at >= intervalMs)) {
      await run()
    }
    schedule()
  }

  const statusText = computed(() => {
    if (suspended()) return 'Live updates paused'
    const at = lastRunAt.value
    if (at === null) return 'Live updates on'
    const seconds = Math.max(0, Math.round((now.value - at) / 1000))
    if (seconds < 10) return 'Updated just now'
    if (seconds < 60) return `Updated ${Math.floor(seconds / 10) * 10}s ago`
    const minutes = Math.floor(seconds / 60)
    return `Updated ${minutes}m ago`
  })

  // Logout must be honoured at once, not up to a full interval later.
  watch(
    () => auth.token,
    (token) => {
      if (!token) {
        clearTimer()
        controller?.abort()
        return
      }
      if (!stopped.value) schedule()
    },
  )

  onMounted(() => {
    mounted = true
    document.addEventListener('visibilitychange', onVisibilityChange)
    clock = window.setInterval(() => {
      now.value = Date.now()
    }, CLOCK_INTERVAL_MS)
    schedule()
  })

  onUnmounted(() => {
    mounted = false
    stopped.value = true
    clearTimer()
    clearDeadline()
    if (clock !== null) {
      window.clearInterval(clock)
      clock = null
    }
    controller?.abort()
    controller = null
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return {
    pause() {
      manualPauses.value += 1
      clearTimer()
    },
    resume() {
      manualPauses.value = Math.max(manualPauses.value - 1, 0)
      if (manualPauses.value === 0) schedule()
    },
    invalidate() {
      generation += 1
      controller?.abort()
    },
    lastRunAt,
    stopped,
    statusText,
  }
}
