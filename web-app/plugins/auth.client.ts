import { useAuthStore } from "@/store/auth";

export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig();

  const auth = useAuthStore();

  return {
    provide: {
      auth,
    },
  };
});
