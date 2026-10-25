import { describe, expect, it } from "vitest";
import type { StatsArm, StatsResponse } from "../api";
import { buildStatsModel } from "./statsModel";

const arm = (
  hits: [number, number, number],
  rate: [number, number, number],
): StatsArm => ({
  hits_top5: { mean: hits[0], sd: hits[1], n_personas: hits[2] },
  false_exclude_rate: { mean: rate[0], sd: rate[1], n_personas: rate[2] },
});

const contract: StatsResponse = {
  arms: {
    base: arm([2.2, 0.8, 5], [0.31, 0.09, 5]),
    base_memory: arm([3.1, 0.7, 5], [0.22, 0.07, 5]),
    updated_memory: arm([3.8, 0.6, 5], [0.15, 0.06, 5]),
  },
};

const only = (a: StatsArm): StatsResponse => ({
  arms: { base: a, base_memory: null, updated_memory: null },
});

describe("buildStatsModel", () => {
  it("returns the contract example in fixed order with fixed labels", () => {
    const m = buildStatsModel(contract);
    expect(m.hits.bars.map((b) => b.label)).toEqual([
      "Base curator",
      "Base + memory",
      "Updated + memory",
    ]);
    expect(m.rate.bars.map((b) => b.id)).toEqual([
      "base",
      "base_memory",
      "updated_memory",
    ]);
    expect(m.hits.bars[0]).toMatchObject({
      missing: false,
      mean: 2.2,
      sd: 0.8,
      n: 5,
      text: "2.2 ± 0.8",
    });
    expect(m.rate.bars[2]).toMatchObject({ mean: 0.15, text: "15% ± 6%" });
    expect(m.hits).toMatchObject({ axisMin: 0, axisMax: 5, n: 5 });
    expect(m.rate).toMatchObject({ axisMin: 0, axisMax: 1, n: 5 });
    expect(m.isEmpty).toBe(false);
    expect(m.updatedMissing).toBe(false);
  });

  it("formats rates as whole percentages", () => {
    const m = buildStatsModel(contract);
    expect(m.rate.bars[0]).toMatchObject({ text: "31% ± 9%" });
    expect(m.rate.bars[1]).toMatchObject({ text: "22% ± 7%" });
  });

  it("marks every arm missing and the model empty when all arms are null", () => {
    const m = buildStatsModel({
      arms: { base: null, base_memory: null, updated_memory: null },
    });
    expect(m.isEmpty).toBe(true);
    expect(m.updatedMissing).toBe(false);
    for (const metric of [m.hits, m.rate]) {
      expect(metric.n).toBeNull();
      for (const bar of metric.bars) {
        expect(bar).toEqual({ id: bar.id, label: bar.label, missing: true });
      }
    }
  });

  it("handles fallback D: updated arm missing, never zero", () => {
    const m = buildStatsModel({
      arms: { ...contract.arms, updated_memory: null },
    });
    expect(m.updatedMissing).toBe(true);
    expect(m.isEmpty).toBe(false);
    expect(m.hits.bars[2]).toEqual({
      id: "updated_memory",
      label: "Updated + memory",
      missing: true,
    });
    expect(m.hits.bars[0].missing).toBe(false);
    expect(m.hits.n).toBe(5);
  });

  it("does not flag updatedMissing when a base arm is also missing", () => {
    const m = buildStatsModel(only(arm([1, 0.5, 5], [0.5, 0.1, 5])));
    expect(m.updatedMissing).toBe(false);
    expect(m.isEmpty).toBe(false);
  });

  it("clips error bars to the axis at both ends", () => {
    const m = buildStatsModel(only(arm([0.3, 0.8, 5], [0.95, 0.1, 5])));
    const hits = m.hits.bars[0];
    expect(hits).toMatchObject({ low: 0, high: 1.1 });
    const top = buildStatsModel(only(arm([4.8, 0.6, 5], [0.02, 0.05, 5])));
    expect(top.hits.bars[0]).toMatchObject({ high: 5 });
    expect(top.hits.bars[0]).toMatchObject({ low: expect.closeTo(4.2, 10) });
    expect(m.rate.bars[0]).toMatchObject({
      high: 1,
      low: expect.closeTo(0.85, 10),
    });
    expect(top.rate.bars[0]).toMatchObject({ low: 0 });
  });

  it("leaves unclipped bars at mean ± sd", () => {
    const b = buildStatsModel(contract).hits.bars[1];
    expect(b).toMatchObject({
      low: expect.closeTo(2.4, 10),
      high: expect.closeTo(3.8, 10),
    });
  });

  it("returns a null shared n when arms disagree, keeping per-arm n", () => {
    const m = buildStatsModel({
      arms: {
        base: arm([2, 0.5, 5], [0.3, 0.1, 5]),
        base_memory: arm([3, 0.5, 4], [0.2, 0.1, 6]),
        updated_memory: null,
      },
    });
    expect(m.hits.n).toBeNull();
    expect(m.rate.n).toBeNull();
    expect(m.hits.bars.map((b) => (b.missing ? null : b.n))).toEqual([
      5,
      4,
      null,
    ]);
    expect(m.rate.bars.map((b) => (b.missing ? null : b.n))).toEqual([
      5,
      6,
      null,
    ]);
  });
});
