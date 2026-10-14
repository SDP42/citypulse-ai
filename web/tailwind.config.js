export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: { colors: {
    ink: "#07090f", panel: "#0d121c", line: "#1c2638", pulse: "#5eead4", warn: "#fbbf24", synth: "#f472b6", muted: "#8a97ad",
  }, fontFamily: { sans: ["Inter", "system-ui", "sans-serif"], mono: ["JetBrains Mono", "ui-monospace", "monospace"] } } },
};
