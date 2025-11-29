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
});