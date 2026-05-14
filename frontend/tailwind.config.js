export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#070a12",
        panel: "rgba(18, 24, 38, 0.78)",
        line: "rgba(148, 163, 184, 0.16)",
        gain: "#2dd4bf",
        loss: "#fb7185",
        amber: "#fbbf24",
      },
      boxShadow: {
        glow: "0 0 40px rgba(45, 212, 191, 0.12)",
      },
    },
  },
  plugins: [],
};
