<!--
  BaseChart.vue
  Thin Chart.js wrapper: owns the canvas lifecycle and applies the shared chart
  chrome. Only the bar and line pieces of Chart.js are registered, and this
  component is imported lazily so Chart.js ships in its own chunk with the
  dashboard only.
  A canvas is opaque to assistive tech, so every chart takes a short
  `chartLabel` and every number it plots also appears in a table on the page -
  the label points at that table rather than reciting hundreds of values.
-->
<template>
  <figure class="m-0">
    <div class="relative w-full" :style="{ height: `${height}px` }">
      <canvas ref="canvasEl" role="img" :aria-label="chartLabel"></canvas>
    </div>
    <figcaption v-if="caption" class="mt-3 text-xs text-zinc-500">{{ caption }}</figcaption>
  </figure>
</template>

<script setup lang="ts" generic="TType extends 'bar' | 'line'">
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
  type ChartConfiguration,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import { INK_SECONDARY } from '../../utils/charts'

Chart.register(
  BarController,
  BarElement,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Legend,
  Tooltip,
)

Chart.defaults.font.family =
  'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
Chart.defaults.font.size = 12
Chart.defaults.color = INK_SECONDARY

const props = defineProps<{
  /** Fixed for the lifetime of the instance; changing it is not supported. */
  type: TType
  data: ChartData<TType>
  options: ChartOptions<TType>
  /** Plot height in px, including room for the axis band. */
  height: number
  /** Short text summary; the detail lives in the table beside the chart. */
  chartLabel: string
  caption?: string
}>()

const canvasEl = ref<HTMLCanvasElement | null>(null)
const chart = shallowRef<Chart<TType> | null>(null)

onMounted(() => {
  const el = canvasEl.value
  if (!el) return
  const config = {
    type: props.type,
    data: props.data,
    options: props.options,
  } as ChartConfiguration<TType>
  chart.value = new Chart<TType>(el, config)
})

watch(
  () => [props.data, props.options] as const,
  ([data, options]) => {
    const instance = chart.value
    if (!instance) return
    instance.data = data
    instance.options = options as typeof instance.options
    instance.update()
  },
)

onBeforeUnmount(() => {
  chart.value?.destroy()
  chart.value = null
})
</script>
