export default defineNuxtPlugin(() => {
  const router = useRouter();
  const { $auth } = useNuxtApp();

  router.beforeEach(async (to, from, next) => {
    if ($auth) {
      let user = await $auth.getUser();
      if (user && !user.subscription) {
        if (to.path !== "/subscribe") {
          return next("/subscribe");
        }
      }
    }

    next();
  });
});
