<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
          Setup
        </h1>
        <p class="text-lg text-foreground/90">Get businessing quickly.</p>
      </div>

      <div
        class="flex flex-col items-start gap-6 max-w-lg"
        v-if="!user.integrations || !user.integrations.ynab"
      >
        <p class="text-lg">
          Although we are not associated with YNAB in any way, they have an
          amazing API that we can use to sync your budget data directly into
          this dashboard.
        </p>
        <p class="text-lg">
          Therefore, this is currently the only supported method to get started.
        </p>

        <NuxtLink to="/auth/ynab">
          <Button class="w-full"> Connect your YNAB account </Button>
        </NuxtLink>
      </div>
      <div v-else class="flex flex-col items-start gap-6 max-w-lg">
        <p class="text-lg">
          Although we are not associated with YNAB in any way, they have an
          amazing API that we can use to sync your plans directly into this
          dashboard.
        </p>
        <p class="text-lg">
          Now that your YNAB account is connected, we can import your plans.
        </p>

        <div v-if="plans.length > 0" class="w-full">
          <form
            @submit.prevent="importPlans"
            class="flex flex-col items-start gap-4 w-full"
          >
            <Label for="plan-ids">Select Plans to Import</Label>
            <Select
              id="plan-ids"
              required
              v-model="selectedPlans"
              multiple
              class="w-full"
            >
              <SelectTrigger class="w-full">
                <SelectValue
                  placeholder="Select plans to import"
                  :value="selectedPlans"
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="plan in plans"
                  :key="plan.id"
                  :value="plan.id"
                >
                  {{ plan.name }}
                </SelectItem>
              </SelectContent>
            </Select>
            <Button type="submit" class="w-full">
              Import Selected Plans
            </Button>
          </form>
        </div>
      </div>
    </main>
  </ClientOnly>
</template>

<script setup>
const { $auth, $api } = useNuxtApp();

let user = computed(() => $auth?.user || { integrations: null });

let plans = ref([]);
let selectedPlans = ref([]);

onMounted(async () => {
  if (user.value.integrations && user.value.integrations.ynab) {
    // Fetch plans from the backend
    try {
      const response = await $api("/api/ynab/plans");
      plans.value = response || [];

      if (plans.value.length === 0) {
        alert("No plans found in your YNAB account.");
      }

      if (plans.value.length === 1) {
        // Auto-select the only available plan
        selectedPlans.value = [plans.value[0].id];
      }
    } catch (error) {
      console.error("Error fetching plans:", error);
      alert("Failed to load plans. Please try again later.");
    }
  }
});
</script>
