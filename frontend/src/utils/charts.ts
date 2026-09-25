// charts.ts
// Shared colour tokens for the admin dashboard charts. Statistics live in
// `utils/stats.ts` - this module is purely about how things are drawn.
//
// Colour is assigned by the job it does, not by taste:
//  - single-series magnitude (counts per TA / per student) -> one blue hue
//  - the 1-5 marking scale is an *ordered* scale -> a single-hue ordinal ramp
//    (light = 1, dark = 5), validated for monotone lightness, visible step
//    gaps and >= 2:1 contrast of the lightest step against the white surface
//  - "nothing recorded yet" is a status, not a series -> the reserved red,
//    and it is always paired with a text label so colour never carries it alone

/** Chart surface; the dashboard cards are white. */
export const CHART_SURFACE = '#ffffff'

/** Categorical slot 1 - the single series hue for count charts. */
export const SERIES_BLUE = '#2a78d6'

/** Reserved status colour for "no evaluations yet". Never used as a series. */
export const STATUS_CRITICAL = '#d03b3b'

/** Text / chrome tokens, aligned with the app's zinc palette. */
export const INK_SECONDARY = '#52525b'
export const INK_MUTED = '#71717a'
export const GRIDLINE = '#e4e4e7'
export const BASELINE = '#d4d4d8'

/** Ordinal ramp for markings 1..5, light -> dark. */
export const MARKING_RAMP: readonly string[] = [
  '#86b6ef',
  '#5598e7',
  '#2a78d6',
  '#1c5cab',
  '#104281',
]

/** Tallest plot we will draw; past this the panel scrolls instead of growing. */
export const MAX_PLOT_HEIGHT = 600

/** Rows a categorical chart will plot before it defers to the table. */
export const MAX_PLOT_ROWS = 20

/**
 * Room for one ~26px row per category plus the axis band, capped so a large
 * roster cannot turn a panel into a several-thousand-pixel scroll.
 */
export function plotHeight(rows: number, extra = 40): number {
  return Math.min(MAX_PLOT_HEIGHT, Math.max(160, rows * 26 + extra))
}
