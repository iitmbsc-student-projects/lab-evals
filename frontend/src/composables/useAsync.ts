// Loading/error state for async work.
// `useAsyncTask` wraps a fetch and tracks `loading` + `error`; `useAsyncAction`
// tracks one-off mutations so a button can disable itself while in flight.
// A cancelled request publishes nothing and keeps `loading` on: the axios
// client hard-redirects on 401, so no error banner or empty state should flash
// on the way out.
import { onMounted, ref, type Ref } from 'vue'
import axios from 'axios'
import { apiErrorMessage } from '../utils/errors'

export interface RunOptions {
  // Re-run without flipping `loading`, so rendered content stays in place
  // instead of collapsing into a spinner.
  silent?: boolean
}

export interface AsyncTask {
  loading: Ref<boolean>
  error: Ref<string>
  run: (options?: RunOptions) => Promise<void>
  // Post-mutation reload: refetch in the background, keeping the current
  // content on screen.
  refresh: () => Promise<void>
}

export interface AsyncTaskOptions {
  // Start with `loading` already true and run the task on mount, so the first
  // render shows the spinner rather than briefly picking the empty branch.
  immediate?: boolean
}

export interface AsyncAction {
  busy: Ref<boolean>
  // Identifies what is currently in flight (a row id, say), so one row can
  // show busy text while the rest only disable.
  busyKey: Ref<string | number | null>
  error: Ref<string>
  run: (mutation: () => Promise<void>, key?: string | number) => Promise<void>
}

// An aborted request is not a failure: the caller gave up on it.
function isCancelled(error: unknown): boolean {
  return axios.isCancel(error) || (error instanceof Error && error.name === 'CanceledError')
}

export function useAsyncTask(task: () => Promise<void>, options: AsyncTaskOptions = {}): AsyncTask {
  const loading = ref(options.immediate === true)
  const error = ref('')
  // Monotonic call id: only the newest run publishes loading/error, so a slow
  // earlier call can never overwrite the state of a later one.
  let latestRun = 0

  async function run(runOptions: RunOptions = {}): Promise<void> {
    const call = ++latestRun
    const ownsSpinner = runOptions.silent !== true
    if (ownsSpinner) loading.value = true
    error.value = ''
    try {
      await task()
    } catch (e: unknown) {
      if (call !== latestRun) return
      // Hold `loading` and stay quiet so the view does not flash an error or
      // an empty state while the client navigates away.
      if (isCancelled(e)) return
      error.value = apiErrorMessage(e)
    }
    if (call === latestRun && ownsSpinner) loading.value = false
  }

  function refresh(): Promise<void> {
    return run({ silent: true })
  }

  if (options.immediate === true) {
    onMounted(() => {
      void run()
    })
  }

  return { loading, error, run, refresh }
}

export function useAsyncAction(): AsyncAction {
  const busy = ref(false)
  const busyKey = ref<string | number | null>(null)
  const error = ref('')

  async function run(mutation: () => Promise<void>, key?: string | number): Promise<void> {
    // One mutation at a time: this is what makes a double-submit a no-op.
    if (busy.value) return
    busy.value = true
    busyKey.value = key ?? null
    error.value = ''
    try {
      await mutation()
    } catch (e: unknown) {
      if (isCancelled(e)) return
      error.value = apiErrorMessage(e)
    }
    busy.value = false
    busyKey.value = null
  }

  return { busy, busyKey, error, run }
}
