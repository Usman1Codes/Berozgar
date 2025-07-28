// tailwind.config.js
module.exports = {
        content: ["./src/**/*.{js,ts,jsx,tsx}"],
        theme: {
          extend: {
            colors: {
              brand: { light: "#FF9248", DEFAULT: "#FF6A00", dark: "#CC5500" },
              background: { light: "#FFFFFF", dark: "#0A0A0A" },
            },
            fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui"] },
          },
        },
        plugins: [],
      };
      