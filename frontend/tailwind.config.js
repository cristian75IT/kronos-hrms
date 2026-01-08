/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
            },
            colors: {
                // Enterprise Palette - Semantic mappings will be handled by DaisyUI themes
                // but we can add specific brand overrides here if needed
            }
        },
    },
    plugins: [
        require('daisyui'),
    ],
    daisyui: {
        themes: [
            {
                light: {
                    ...require("daisyui/src/theming/themes")["light"],
                    "primary": "#4f46e5", // Indigo 600
                    "primary-focus": "#4338ca", // Indigo 700
                    "secondary": "#64748b", // Slate 500
                    "accent": "#0ea5e9", // Sky 500
                    "neutral": "#334155", // Slate 700
                    "base-100": "#ffffff",
                    "base-200": "#f8fafc", // Slate 50
                    "base-300": "#f1f5f9", // Slate 100
                    "info": "#3b82f6",
                    "success": "#22c55e",
                    "warning": "#f59e0b",
                    "error": "#ef4444",
                    "--rounded-box": "0.5rem", // slightly tighter radius
                    "--rounded-btn": "0.375rem",
                },
            },
        ],
        darkTheme: "light", // Enforce light mode for now for consistency, or add dark theme later
    },
}
