import type { StatsResponse, StatSummary } from "../api";

export type MetricId = "hits_top5" | "false_exclude_rate";
type ArmId = keyof StatsResponse["arms"];

export type Bar =
  | {
      id: ArmId;
      label: string;
      missing: false;
      mean: number;
      sd: number;
      n: number;
      low: number;
      high: number;
      text: string;
    }
  | { id: ArmId; label: string; missing: true };

export type MetricModel = {
  id: MetricId;
  axisMin: number;
  axisMax: number;
  bars: Bar[];
  n: number | null;
};

export type StatsModel = {
  hits: MetricModel;
  rate: MetricModel;
  isEmpty: boolean;
  updatedMissing: boolean;
};

const ARMS: { id: ArmId; label: string }[] = [
  { id: "base", label: "Base curator" },
  { id: "base_memory", label: "Base + memory" },
  { id: "updated_memory", label: "Updated + memory" },
];

const pct = (x: number) => `${Math.round(x * 100)}%`;

const METRICS: Record<
  MetricId,
  { axisMax: number; text: (s: StatSummary) => string }
> = {
  hits_top5: {
    axisMax: 5,
    text: (s) => `${s.mean.toFixed(1)} ± ${s.sd.toFixed(1)}`,
  },
  false_exclude_rate: {
    axisMax: 1,
    text: (s) => `${pct(s.mean)} ± ${pct(s.sd)}`,
  },
};

function buildMetric(stats: StatsResponse, id: MetricId): MetricModel {
  const { axisMax, text } = METRICS[id];
  const bars: Bar[] = ARMS.map(({ id: armId, label }) => {
    const arm = stats.arms[armId];
    if (!arm) return { id: armId, label, missing: true };
    const s = arm[id];
    return {
      id: armId,
      label,
      missing: false,
      mean: s.mean,
      sd: s.sd,
      n: s.n_personas,
      low: Math.max(0, s.mean - s.sd),
      high: Math.min(axisMax, s.mean + s.sd),
      text: text(s),
    };
  });
  const ns = new Set(bars.flatMap((b) => (b.missing ? [] : [b.n])));
  return {
    id,
    axisMin: 0,
    axisMax,
    bars,
    n: ns.size === 1 ? [...ns][0] : null,
  };
}

export function buildStatsModel(stats: StatsResponse): StatsModel {
  const { base, base_memory, updated_memory } = stats.arms;
  return {
    hits: buildMetric(stats, "hits_top5"),
    rate: buildMetric(stats, "false_exclude_rate"),
    isEmpty: !base && !base_memory && !updated_memory,
    updatedMissing: !!base && !!base_memory && !updated_memory,
  };
}
