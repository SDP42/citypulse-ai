import { render, screen } from "@testing-library/react";
import { DataModeBadge } from "./DataModeBadge";

const base = { status: "ok", version: "0", network: "off", llm_provider: "none" };

it("always labels synthetic data loudly", () => {
  render(<DataModeBadge health={{ ...base, data_mode: "synthetic" }} />);
  expect(screen.getByText("SYNTHETIC DEMO DATA")).toBeInTheDocument();
});
it("labels real data and never claims a mode when the API is unreachable", () => {
  const { rerender } = render(<DataModeBadge health={{ ...base, data_mode: "real" }} />);
  expect(screen.getByText("REAL DATA")).toBeInTheDocument();
  rerender(<DataModeBadge health={undefined} />);
  expect(screen.getByText(/API offline/)).toBeInTheDocument();
});
