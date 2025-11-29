<template>
  <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
    <div class="mb-12">
      <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
        Subscribe
      </h1>
    </div>

    <div class="relative bg-muted rounded-full p-1 mb-8 max-w-xs">
      <div
        :class="`absolute top-1 bottom-1 rounded-full transition-all duration-300 ${
          billingRequested === 'annual'
            ? 'left-1 right-1/2 bg-primary shadow-glow'
            : 'left-1/2 right-1 bg-primary shadow-glow'
        }`"
      />
      <div class="relative flex">
        <button
          @click="billingRequested = 'annual'"
          :class="`flex-1 py-2 px-4 text-sm font-medium rounded-full transition-colors ${
            billingRequested === 'annual'
              ? 'text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
          }`"
        >
          Annual
        </button>
        <button
          type="button"
          @click="billingRequested = 'monthly'"
          :class="`flex-1 py-2 px-4 text-sm font-medium rounded-full transition-colors ${
            billingRequested === 'monthly'
              ? 'text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
          }`"
        >
          Monthly
        </button>
      </div>
    </div>

    <Card class="w-full max-w-xs">
      <CardContent class="flex flex-col p-6 gap-4">
        <CardTitle class="font-bold text-2xl">Professional</CardTitle>

        <p></p>
        <div>
          <p>
            <span class="font-bold text-2xl"
              >${{ pricing[billingRequested] }}
            </span>
            <span class="text-foreground/80">{{
              billingRequested === "annual"
                ? "/year billed annually"
                : "/month month-to-month"
            }}</span>
          </p>
          <p class="text-sm text-foreground/80" v-if="shouldOfferTrial">
            Free 14-day trial. No credit card required.
          </p>
        </div>

        <ClientOnly>
          <Button class="w-full" size="lg"> Subscribe Now </Button>
          <Button
            class="w-full"
            size="lg"
            variant="ghost"
            @click="startTrial()"
            v-if="shouldOfferTrial"
          >
            Start Trial
          </Button>
          <Button disabled variant="ghost" v-else-if="trialActive">
            Trial Active
          </Button>
        </ClientOnly>
      </CardContent>
    </Card>
  </main>
</template>

<script setup>
const { $auth, $api } = useNuxtApp();

const user = computed(() => $auth?.user || {});

const billingRequested = ref("annual");
const shouldOfferTrial = computed(() => {
  return !user.value.subscription;
});

const trialActive = computed(() => {
  return (
    user.value.subscription && user.value.subscription.status === "trialing"
  );
});

onMounted(async () => {
  if ($auth) {
    let user = await $auth.user;
    if (user) {
      billingRequested.value = user.requestedBillingPeriod || "annual";
    }
  }
});

async function startTrial() {
  try {
    if ($auth && $auth.user) {
      await $api("/users/me/start-trial", {
        method: "POST",
      });
      shouldOfferTrial.value = false;

      // TODO: Figure out where to go from here.
    }
  } catch (error) {
    console.error("Error starting trial:", error);
    alert("There was an error starting your trial. Please try again later.");
  }
}
let pricing = {
  annual: "99",
  monthly: "9.90",
};
</script>
