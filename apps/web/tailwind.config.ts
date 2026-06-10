import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        panel: "#f5f7fa",
        border: "#d5dae1",
        accent: "#1f4ea3",
        textMain: "#0e1525",
        textMuted: "#5b6472"
      }
    }
  },
  plugins: []
};

export default config;
