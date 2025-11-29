// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: [
    "@nuxtjs/google-fonts",
    "@nuxtjs/tailwindcss",
    "shadcn-nuxt",
    "@pinia/nuxt",
    "@nuxt/scripts",
  ],
  googleFonts: {
    families: {
      "Old Standard TT": [400, 500, 600, 700],
    },
  },
  shadcn: {
    prefix: "",
    componentDir: "./components/ui",
  },
  vite: {
    server: {
      port: 3040,
      proxy: {
        "/api": {
          target: "http://127.0.0.1:8040",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  },
});
