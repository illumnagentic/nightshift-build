import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { BarChart } from "./BarChart";
import {
  buildStatsModel,
  type MetricModel,
  type StatsModel,
} from "./statsModel";
import "./dashboard.css";

const NETWORK_MESSAGE = "Could not reach the server. Try again.";
const percent = (v: number) => `${Math.round(v * 100)}%`;

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; model: StatsModel };

function ChartNotes({ metric }: { metric: MetricModel }) {
  return (
    <>
      {metric.n !== null && (
        <p className="dashboard__caption">
          Across {metric.n} held-out personas
        </p>
      )}
      <p className="dashboard__caption">
        Error bars: ±1 standard deviation across held-out personas.
      </p>
    </>
  );
}

export default function DashboardScreen() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((a) => a + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .getStats()
      .then((stats) => {
        if (!cancelled)
          setState({ status: "ready", model: buildStatsModel(stats) });
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setState({
            status: "error",
            message: err instanceof ApiError ? err.message : NETWORK_MESSAGE,
          });
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  if (state.status === "loading")
    return (
      <div className="dashboard">
        <p>Loading…</p>
      </div>
    );

  if (state.status === "error")
    return (
      <div className="dashboard">
        <p role="alert">{state.message}</p>
        <button type="button" onClick={retry}>
          Retry
        </button>
      </div>
    );

  const { model } = state;
  if (model.isEmpty)
    return (
      <div className="dashboard">
        <p>No evaluation has run yet.</p>
      </div>
    );

  return (
    <div className="dashboard">
      {import.meta.env.VITE_API_MODE === "mock" && (
        <p className="dashboard__banner">
          Sample numbers from the mock, not real results
        </p>
      )}
      {model.updatedMissing && (
        <p className="dashboard__note">
          The updated curator is not available, so only the base arms are shown.
        </p>
      )}
      <section>
        <h2>Hits in the top 5</h2>
        <p className="dashboard__caption">
          Of the curator's five highest-ranked held-out listings, how many the
          persona's hidden rules count as good.
        </p>
        <BarChart metric={model.hits} title="Hits in the top 5" />
        <ChartNotes metric={model.hits} />
      </section>
      <section>
        <h2>False-exclude rate</h2>
        <p className="dashboard__caption">
          Share of rule-good listings ranked below the cut.
        </p>
        <BarChart
          metric={model.rate}
          title="False-exclude rate"
          format={percent}
        />
        <ChartNotes metric={model.rate} />
      </section>
    </div>
  );
}
