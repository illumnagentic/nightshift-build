import { useState } from "react";
import type { MetricModel } from "./statsModel";
import "./dashboard.css";

type Props = {
  metric: MetricModel;
  title: string;
  format?: (v: number) => string;
};

const W = 480;
const H = 270;
const LEFT = 44;
const RIGHT = 12;
const TOP = 30;
const BASE = 230;
const BAR_W = 24;
const R = 4;
const CAP = 5;
const TIP_W = 132;
const TIP_H = 70;

const defaultFormat = (v: number) => String(Math.round(v * 10) / 10);

export function BarChart({ metric, title, format = defaultFormat }: Props) {
  const [active, setActive] = useState<number | null>(null);
  const [showTable, setShowTable] = useState(false);
  const { axisMin, axisMax, bars } = metric;

  const y = (v: number) =>
    BASE - ((v - axisMin) / (axisMax - axisMin)) * (BASE - TOP);
  const slot = (W - LEFT - RIGHT) / bars.length;
  const cx = (i: number) => LEFT + slot * i + slot / 2;

  const tickCount = axisMax > 1 ? axisMax : 2;
  const ticks = Array.from(
    { length: tickCount + 1 },
    (_, i) => axisMin + ((axisMax - axisMin) * i) / tickCount,
  );

  const summary = bars
    .map((b) =>
      b.missing ? `${b.label}: not available` : `${b.label}: ${b.text}`,
    )
    .join(". ");
  const label = `${title}. ${summary}.${metric.n === null ? "" : ` Across ${metric.n} personas.`}`;

  const activeBar = active === null ? null : bars[active];
  const tipX =
    active === null
      ? 0
      : Math.min(W - RIGHT - TIP_W, Math.max(LEFT, cx(active) - TIP_W / 2));

  return (
    <div className="dashboard chart">
      <svg
        className="chart__svg"
        viewBox={`0 0 ${W} ${H}`}
        role="group"
        aria-label={label}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line
              className={t === axisMin ? "chart__axis" : "chart__grid"}
              x1={LEFT}
              x2={W - RIGHT}
              y1={y(t)}
              y2={y(t)}
            />
            <text
              className="chart__tick"
              x={LEFT - 8}
              y={y(t)}
              textAnchor="end"
              dominantBaseline="middle"
            >
              {format(t)}
            </text>
          </g>
        ))}
        {bars.map((b, i) => {
          const x = cx(i) - BAR_W / 2;
          return (
            <g key={b.id}>
              {b.missing ? (
                <text
                  className="chart__missing"
                  x={cx(i)}
                  y={BASE - 10}
                  textAnchor="middle"
                >
                  Not available
                </text>
              ) : (
                <>
                  {b.mean > axisMin && (
                    <path
                      className="chart__bar"
                      d={barPath(x, y(b.mean), BASE)}
                    />
                  )}
                  <path
                    className="chart__err-halo"
                    d={errPath(cx(i), y(b.low), y(b.high))}
                  />
                  <path
                    className="chart__err"
                    d={errPath(cx(i), y(b.low), y(b.high))}
                  />
                  <text
                    className="chart__value"
                    x={cx(i)}
                    y={y(b.high) - 8}
                    textAnchor="middle"
                  >
                    {b.text}
                  </text>
                </>
              )}
              <text
                className="chart__label"
                x={cx(i)}
                y={BASE + 22}
                textAnchor="middle"
              >
                {b.label}
              </text>
              <rect
                className="chart__hit"
                x={cx(i) - slot / 2}
                y={TOP - 20}
                width={slot}
                height={BASE - TOP + 20}
                role="img"
                tabIndex={0}
                aria-label={
                  b.missing
                    ? `${b.label}: not available`
                    : `${b.label}: ${b.text}, ${b.n} personas`
                }
                onPointerEnter={() => setActive(i)}
                onPointerLeave={() => setActive(null)}
                onFocus={() => setActive(i)}
                onBlur={() => setActive(null)}
              />
            </g>
          );
        })}
        {activeBar && (
          <g className="chart__tip" transform={`translate(${tipX} ${TOP})`}>
            <rect width={TIP_W} height={TIP_H} rx={4} />
            <text x={8} y={16} className="chart__tip-label">
              {activeBar.label}
            </text>
            {activeBar.missing ? (
              <text x={8} y={36} className="chart__tip-value">
                Not available
              </text>
            ) : (
              <>
                <text x={8} y={34} className="chart__tip-value">
                  Mean {format(activeBar.mean)}
                </text>
                <text x={8} y={50} className="chart__tip-value">
                  SD {format(activeBar.sd)}
                </text>
                <text x={8} y={64} className="chart__tip-label">
                  Personas {activeBar.n}
                </text>
              </>
            )}
          </g>
        )}
      </svg>
      <button
        type="button"
        className="chart__toggle"
        aria-expanded={showTable}
        onClick={() => setShowTable((s) => !s)}
      >
        {showTable ? "Hide table" : "Show table"}
      </button>
      {showTable && (
        <table className="chart__table">
          <caption>{title}</caption>
          <thead>
            <tr>
              <th scope="col">Arm</th>
              <th scope="col">Mean</th>
              <th scope="col">Standard deviation</th>
              <th scope="col">Personas</th>
            </tr>
          </thead>
          <tbody>
            {bars.map((b) => (
              <tr key={b.id}>
                <th scope="row">{b.label}</th>
                {b.missing ? (
                  <td colSpan={3}>Not available</td>
                ) : (
                  <>
                    <td>{format(b.mean)}</td>
                    <td>{format(b.sd)}</td>
                    <td>{b.n}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function barPath(x: number, top: number, base: number) {
  const r = Math.min(R, base - top);
  const x2 = x + BAR_W;
  return `M${x} ${base}V${top + r}A${r} ${r} 0 0 1 ${x + r} ${top}H${x2 - r}A${r} ${r} 0 0 1 ${x2} ${top + r}V${base}Z`;
}

function errPath(x: number, yLow: number, yHigh: number) {
  return `M${x} ${yLow}V${yHigh}M${x - CAP} ${yLow}H${x + CAP}M${x - CAP} ${yHigh}H${x + CAP}`;
}
