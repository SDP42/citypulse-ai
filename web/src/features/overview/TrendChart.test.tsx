import { fireEvent, render, screen } from "@testing-library/react";
import { TrendChart } from "./TrendChart";

const trend = (series: { start: string; count: number; no_reports: boolean }[]) =>
  ({ granularity: "day", timezone: "Asia/Kolkata", dated_total: 3, undated: 0, series });

it("says 'no data' (not 'no problems' or zero bars) when there is no series", () => {
  render(<TrendChart trend={trend([])} onTrace={() => {}} />);
  expect(screen.getByText(/no data”, not “no problems/)).toBeInTheDocument();
});

it("marks gap buckets as 'no reports recorded', never as a count of zero events", () => {
  render(<TrendChart trend={trend([{ start: "2026-08-01", count: 2, no_reports: false }, { start: "2026-08-02", count: 0, no_reports: true }, { start: "2026-08-03", count: 1, no_reports: false }])} onTrace={() => {}} />);
  expect(screen.getByText("2026-08-02: no reports recorded")).toBeInTheDocument();
  expect(screen.getByText("2026-08-01: 2 reports")).toBeInTheDocument();
  expect(screen.getByText("2026-08-03: 1 report")).toBeInTheDocument();
  expect(screen.getAllByText("no reports recorded").length).toBeGreaterThan(0); // table fallback
});

it("opens the trace when the chart is clicked", () => {
  const onTrace = vi.fn();
  render(<TrendChart trend={trend([{ start: "2026-08-01", count: 1, no_reports: false }])} onTrace={onTrace} />);
  fireEvent.click(screen.getByRole("img"));
  expect(onTrace).toHaveBeenCalledOnce();
});
