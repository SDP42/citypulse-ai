import { describe as suite, expect, it } from "vitest";
import { describe, formatWhen, sniffHeaders } from "./format";

suite("format", () => {
  it("explains known codes and passes unknown ones through", () => {
    expect(describe("coords_possibly_swapped")).toMatch(/not auto-corrected/);
    expect(describe("brand_new_code")).toBe("brand_new_code");
  });
  it("shows unknown time as unknown, never as a date", () => {
    expect(formatWhen(null, "unknown")).toBe("unknown");
    expect(formatWhen("2026-08-02", "day")).toBe("2026-08-02");
    expect(formatWhen("2026-08-03T03:30:00+00:00", "minute")).toMatch(/IST/);
  });
  it("sniffs headers for comma, semicolon and tab files", () => {
    expect(sniffHeaders('id,"Type",lat\n1,a,2')).toEqual(["id", "Type", "lat"]);
    expect(sniffHeaders("a;b;c\n1;2;3")).toEqual(["a", "b", "c"]);
    expect(sniffHeaders("a\tb\n1\t2")).toEqual(["a", "b"]);
  });
});
