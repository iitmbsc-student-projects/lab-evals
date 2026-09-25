// stats.ts
// Domain statistics for the 1-5 marking scale, shared by the dashboard's
// tables and its charts. Kept out of `charts.ts` on purpose: these are facts
// about evaluations, not about rendering.

/** The valid markings, in order. */
export const MARKINGS = [1, 2, 3, 4, 5] as const

/** Aggregated evaluation activity for one person on one lab slot. */
export interface PersonStats {
  id: number
  name: string
  email: string
  /** False for someone who has evaluations here but is not on the roster. */
  onRoster: boolean
  total: number
  /** Counts of markings 1..5; index 0 holds marking 1. */
  dist: number[]
  mean: number | null
  /** TAs only: how many distinct students they touched. */
  studentsCovered: number
}

/** A zeroed 1..5 distribution. Index 0 holds the count of marking 1. */
export function emptyDistribution(): number[] {
  return [0, 0, 0, 0, 0]
}

/**
 * Increment the bucket for `marking`. The backend constrains markings to 1-5;
 * this guard is defence in depth so a stray value can never create a `-1`
 * property or a sixth bucket that every consumer would then mis-read.
 */
export function bumpDistribution(dist: number[], marking: number): void {
  const index = marking - 1
  if (!Number.isInteger(index) || index < 0 || index >= MARKINGS.length) return
  dist[index] = (dist[index] ?? 0) + 1
}

/** Mean of a 1..5 distribution, or null when nothing was recorded. */
export function distributionMean(dist: readonly number[]): number | null {
  const total = dist.reduce((sum, n) => sum + n, 0)
  if (total === 0) return null
  const weighted = dist.reduce((sum, n, i) => sum + n * (i + 1), 0)
  return weighted / total
}

/** Percentage of `part` within `total`, 0 when there is nothing to divide. */
export function percentage(part: number, total: number): number {
  return total === 0 ? 0 : (part / total) * 100
}

/**
 * Integer percentages that always sum to 100 (largest-remainder / Hare quota).
 * Rounding each share on its own lets `[1, 1, 1, 0, 0]` print as 33/33/33 = 99,
 * which invites the reader to spot a bug that isn't there.
 */
export function apportionPercentages(counts: readonly number[], total: number): number[] {
  if (total <= 0) return counts.map(() => 0)
  const exact = counts.map((count) => percentage(count, total))
  const floors = exact.map((value) => Math.floor(value))
  let remaining = 100 - floors.reduce((sum, n) => sum + n, 0)
  const order = exact
    .map((value, index) => ({ index, remainder: value - Math.floor(value) }))
    // Ties go to the earlier (lower) marking so the result is deterministic.
    .sort((a, b) => b.remainder - a.remainder || a.index - b.index)
  for (const entry of order) {
    if (remaining <= 0) break
    floors[entry.index] = (floors[entry.index] ?? 0) + 1
    remaining -= 1
  }
  return floors
}

/** A mean rendered for display; an em dash when there is nothing to average. */
export function formatMean(mean: number | null): string {
  return mean === null ? '—' : mean.toFixed(2)
}
