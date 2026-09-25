<!--
  PersonStatsPanel.vue
  One section of the admin dashboard: the charts and the pivot table for a set
  of people (TAs or students) on a single lab slot. Both audiences consume the
  same `PersonStats` rows and asked the same three questions - how much, how
  generously, and who is missing - so they share one component rather than two
  near-identical copies of the same 150 lines of template.

  Charts plot at most `MAX_PLOT_ROWS` rows and the height is capped; the table
  below always carries the complete list.
-->
<template>
  <section class="mb-8" :aria-labelledby="headingId">
    <h3 :id="headingId" class="text-lg font-semibold text-zinc-900 mb-1">{{ heading }}</h3>
    <p class="text-sm text-zinc-600 mb-4">{{ description }}</p>

    <div
      v-if="rows.length === 0"
      class="rounded-lg border border-zinc-200 bg-white p-10 text-center shadow-sm"
    >
      <h4 class="text-sm font-medium text-zinc-900">{{ emptyTitle }}</h4>
      <p class="mt-1 text-sm text-zinc-500">{{ emptyMessage }}</p>
    </div>

    <template v-else>
      <div class="grid gap-4" :class="chartCount > 1 ? 'lg:grid-cols-2' : ''">
        <div
          v-if="showCountChart"
          class="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm overflow-hidden"
        >
          <h4 class="text-sm font-semibold text-zinc-900 mb-4">{{ countChartHeading }}</h4>
          <BaseChart
            type="bar"
            :data="countData"
            :options="countOptions"
            :height="plotHeight(chartRows.length)"
            :chart-label="`Bar chart of ${countLabel.toLowerCase()} per ${personLabel.toLowerCase()}; the table below lists the values.`"
            :caption="withTruncationNote(countChartCaption, chartRows.length)"
          />
        </div>

        <div class="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm overflow-hidden">
          <h4 class="text-sm font-semibold text-zinc-900 mb-4">{{ marksChartHeading }}</h4>
          <div v-if="markRows.length === 0" class="py-10 text-center">
            <p class="text-sm text-zinc-500">
              No {{ personLabel.toLowerCase() }} has an evaluation yet.
            </p>
          </div>
          <BaseChart
            v-else
            type="bar"
            :data="marksData"
            :options="marksOptions"
            :height="plotHeight(markRows.length, 64)"
            :chart-label="`Stacked bar chart of markings per ${personLabel.toLowerCase()}; the table below lists the values.`"
            :caption="withTruncationNote(marksChartCaption, markRows.length)"
          />
        </div>

        <div
          v-if="showMeanChart"
          class="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm overflow-hidden"
        >
          <h4 class="text-sm font-semibold text-zinc-900 mb-4">{{ meanChartHeading }}</h4>
          <div v-if="meanRows.length === 0" class="py-10 text-center">
            <p class="text-sm text-zinc-500">
              A mean appears once a {{ personLabel.toLowerCase() }} has marked something.
            </p>
          </div>
          <BaseChart
            v-else
            type="line"
            :data="meanData"
            :options="meanOptions"
            :height="plotHeight(meanRows.length, 64)"
            :chart-label="`Dot plot of the mean mark per ${personLabel.toLowerCase()} on a 1 to 5 axis; the table below lists the values.`"
            :caption="withTruncationNote(meanChartCaption, meanRows.length)"
          />
        </div>
      </div>

      <div class="mt-4 overflow-x-auto">
        <AppTable>
          <template #head>
            <th scope="col">{{ personLabel }}</th>
            <th scope="col">{{ countLabel }}</th>
            <th v-if="expectedPerPerson !== undefined" scope="col">Of expected</th>
            <th v-if="showStudentsCovered" scope="col">Students covered</th>
            <th scope="col">Mean mark</th>
            <th v-for="m in MARKINGS" :key="m" scope="col">{{ m }} / 5</th>
          </template>
          <tr v-for="row in tableRows" :key="row.id" :class="row.total === 0 ? 'bg-red-50' : ''">
            <td>
              <span class="font-medium text-zinc-900">{{ row.name }}</span>
              <span class="block text-xs text-zinc-500">{{ row.email }}</span>
              <AppBadge v-if="!row.onRoster" variant="warning" size="sm" class="mt-1">
                Not on roster
              </AppBadge>
            </td>
            <td>
              <AppBadge v-if="row.total === 0" variant="danger" size="sm">None yet</AppBadge>
              <span v-else class="tabular-nums">{{ row.total }}</span>
            </td>
            <td v-if="expectedPerPerson !== undefined" class="tabular-nums">
              <!-- Nothing is expected of someone who is no longer on the roster. -->
              {{ row.onRoster ? expectedPerPerson : '—' }}
            </td>
            <td v-if="showStudentsCovered" class="tabular-nums">{{ row.studentsCovered }}</td>
            <td class="tabular-nums">{{ formatMean(row.mean) }}</td>
            <td v-for="(count, i) in row.dist" :key="i" class="tabular-nums">
              {{ count }}
              <span v-if="row.shares" class="text-zinc-500">({{ row.shares[i] }}%)</span>
            </td>
          </tr>
        </AppTable>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import type { ChartData, ChartOptions, ScriptableScaleContext } from 'chart.js'
import AppBadge from '../common/AppBadge.vue'
import AppTable from '../common/AppTable.vue'
import {
  BASELINE,
  CHART_SURFACE,
  GRIDLINE,
  INK_MUTED,
  INK_SECONDARY,
  MARKING_RAMP,
  MAX_PLOT_ROWS,
  SERIES_BLUE,
  STATUS_CRITICAL,
  plotHeight,
} from '../../utils/charts'
import {
  MARKINGS,
  apportionPercentages,
  formatMean,
  percentage,
  type PersonStats,
} from '../../utils/stats'

// Kept async so Chart.js stays in its own chunk rather than being pulled into
// whatever statically imports this panel.
const BaseChart = defineAsyncComponent(() => import('./BaseChart.vue'))

const props = withDefaults(
  defineProps<{
    heading: string
    headingId: string
    description: string
    /** Complete, already-sorted list. The table shows all of it. */
    rows: readonly PersonStats[]
    /** Singular noun for one person, e.g. "TA". */
    personLabel: string
    /** Header for the total-evaluations column. */
    countLabel: string
    emptyTitle: string
    emptyMessage: string
    /** Stack the 1-5 breakdown as raw counts or as a share of each row. */
    stackedMode: 'count' | 'percent'
    marksChartHeading: string
    marksChartCaption?: string
    showCountChart?: boolean
    countChartHeading?: string
    countChartCaption?: string
    showMeanChart?: boolean
    meanChartHeading?: string
    meanChartCaption?: string
    /** Reference line for the mean dot plot: the slot-wide mean. */
    meanReference?: number | null
    showStudentsCovered?: boolean
    /** Pass a number to render an "Of expected" column. */
    expectedPerPerson?: number
    /** Show each row's 1-5 counts as apportioned percentages too. */
    showShares?: boolean
  }>(),
  {
    marksChartCaption: undefined,
    showCountChart: false,
    countChartHeading: '',
    countChartCaption: undefined,
    showMeanChart: false,
    meanChartHeading: '',
    meanChartCaption: undefined,
    meanReference: null,
    showStudentsCovered: false,
    expectedPerPerson: undefined,
    showShares: false,
  },
)

const chartCount = computed(
  () => 1 + (props.showCountChart ? 1 : 0) + (props.showMeanChart ? 1 : 0),
)

/** Rows the count chart plots: the head of the caller's ordering. */
const chartRows = computed(() => props.rows.slice(0, MAX_PLOT_ROWS))

/** A share of nothing is meaningless, so percent mode drops empty rows. */
const markRows = computed(() => {
  const base =
    props.stackedMode === 'percent' ? props.rows.filter((row) => row.total > 0) : props.rows
  return base.slice(0, MAX_PLOT_ROWS)
})

const meanRows = computed(() =>
  props.rows.filter((row) => row.mean !== null).slice(0, MAX_PLOT_ROWS),
)

const tableRows = computed(() =>
  props.rows.map((row) => ({
    ...row,
    shares: props.showShares && row.total > 0 ? apportionPercentages(row.dist, row.total) : null,
  })),
)

function withTruncationNote(caption: string | undefined, plotted: number): string | undefined {
  const hidden = props.rows.length - plotted
  if (hidden <= 0) return caption
  const note = `Charting the first ${plotted} of ${props.rows.length}; the table below lists every ${props.personLabel.toLowerCase()}.`
  return caption ? `${caption} ${note}` : note
}

/** Red tick labels flag the people with nothing recorded; the table says so in words. */
function tickColour(rows: readonly PersonStats[]) {
  return (context: ScriptableScaleContext) =>
    rows[context.index]?.total === 0 ? STATUS_CRITICAL : INK_SECONDARY
}

const countData = computed<ChartData<'bar'>>(() => ({
  labels: chartRows.value.map((row) => row.name),
  datasets: [
    {
      label: props.countLabel,
      data: chartRows.value.map((row) => row.total),
      backgroundColor: chartRows.value.map((row) =>
        row.total === 0 ? STATUS_CRITICAL : SERIES_BLUE,
      ),
      // A zero is a real answer here, so give it a visible stub rather than an
      // empty row the eye slides past.
      minBarLength: 3,
      maxBarThickness: 24,
      borderRadius: 4,
      borderSkipped: 'start',
    },
  ],
}))

const countOptions = computed<ChartOptions<'bar'>>(() => ({
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: {
    legend: { display: false },
    tooltip: { displayColors: false },
  },
  scales: {
    x: {
      beginAtZero: true,
      suggestedMax: 4,
      ticks: { precision: 0, color: INK_MUTED },
      grid: { color: GRIDLINE },
      border: { color: BASELINE },
    },
    y: {
      ticks: { color: tickColour(chartRows.value), autoSkip: false },
      grid: { display: false },
      border: { color: BASELINE },
    },
  },
}))

const marksData = computed<ChartData<'bar'>>(() => {
  const rows = markRows.value
  const asPercent = props.stackedMode === 'percent'
  return {
    labels: rows.map((row) => row.name),
    datasets: MARKINGS.map((marking, index) => ({
      label: `${marking} / 5`,
      data: rows.map((row) =>
        asPercent ? percentage(row.dist[index] ?? 0, row.total) : (row.dist[index] ?? 0),
      ),
      backgroundColor: MARKING_RAMP[index],
      // Inset only the trailing edge: a box on all four sides eats a thin
      // segment alive, so a single 5/5 could read as "never gave a 5".
      borderColor: CHART_SURFACE,
      borderWidth: { top: 0, right: 1, bottom: 0, left: 0 },
      borderSkipped: false,
      maxBarThickness: 24,
    })),
  }
})

const marksOptions = computed<ChartOptions<'bar'>>(() => {
  const rows = markRows.value
  const asPercent = props.stackedMode === 'percent'
  return {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: {
        position: 'top',
        align: 'start',
        labels: {
          color: INK_SECONDARY,
          usePointStyle: true,
          pointStyle: 'circle',
          boxWidth: 8,
          boxHeight: 8,
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const row = rows[context.dataIndex]
            const count = row ? (row.dist[context.datasetIndex] ?? 0) : 0
            if (!asPercent) return `${context.dataset.label}: ${count}`
            // The same apportionment the table prints, so the two agree.
            const share = row ? apportionPercentages(row.dist, row.total)[context.datasetIndex] : 0
            return `${context.dataset.label}: ${count} (${share}%)`
          },
        },
      },
    },
    scales: {
      x: {
        stacked: true,
        beginAtZero: true,
        min: 0,
        max: asPercent ? 100 : undefined,
        ticks: {
          precision: asPercent ? undefined : 0,
          color: INK_MUTED,
          callback: (value: string | number) => (asPercent ? `${value}%` : `${value}`),
        },
        grid: { color: GRIDLINE },
        border: { color: BASELINE },
      },
      y: {
        stacked: true,
        ticks: { color: tickColour(rows), autoSkip: false },
        grid: { display: false },
        border: { color: BASELINE },
      },
    },
  }
})

// The mean dot plot: one row per person, a dot at their mean on a shared 1-5
// axis, with the slot mean as a dashed reference line. It answers "is anyone
// marking harder than the rest" in about a second.
const meanData = computed<ChartData<'line'>>(() => {
  const rows = meanRows.value
  const reference = props.meanReference
  const datasets: ChartData<'line'>['datasets'] = [
    {
      label: 'Mean mark',
      data: rows.map((row) => row.mean ?? 0),
      showLine: false,
      pointRadius: 5,
      pointHoverRadius: 7,
      pointBackgroundColor: SERIES_BLUE,
      pointBorderColor: CHART_SURFACE,
      pointBorderWidth: 2,
    },
  ]
  if (reference !== null && reference !== undefined) {
    datasets.push({
      label: `Slot mean (${reference.toFixed(2)})`,
      data: rows.map(() => reference),
      borderColor: INK_MUTED,
      borderWidth: 1.5,
      borderDash: [4, 4],
      pointRadius: 0,
      pointHoverRadius: 0,
    })
  }
  return { labels: rows.map((row) => row.name), datasets }
})

const meanOptions = computed<ChartOptions<'line'>>(() => {
  const rows = meanRows.value
  return {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: {
        position: 'top',
        align: 'start',
        labels: {
          color: INK_SECONDARY,
          usePointStyle: true,
          pointStyle: 'circle',
          boxWidth: 8,
          boxHeight: 8,
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            if (context.datasetIndex !== 0) return context.dataset.label ?? ''
            const row = rows[context.dataIndex]
            if (!row) return ''
            return `Mean ${formatMean(row.mean)} over ${row.total} evaluations`
          },
        },
      },
    },
    scales: {
      x: {
        min: 1,
        max: 5,
        ticks: { stepSize: 1, color: INK_MUTED },
        grid: { color: GRIDLINE },
        border: { color: BASELINE },
      },
      y: {
        ticks: { color: INK_SECONDARY, autoSkip: false },
        grid: { display: false },
        border: { color: BASELINE },
      },
    },
  }
})
</script>
