export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig();

  const api = $fetch.create({
    baseURL: config.apiBase || "/api",
  });

  // Expose to useNuxtApp().$api
  return {
    provide: {
      api,
    },
  };
});
