<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
          Setup
        </h1>
        <p class="text-lg text-foreground/90">Import your data here.</p>
      </div>

      <div class="flex flex-col items-start gap-6 max-w-lg">
        <p class="text-lg">
          Although we are not associated with YNAB in any way, they have an
          amazing API that we can use to sync your plans directly into this
          dashboard.
        </p>
        <p class="text-lg">
          Now that your YNAB account is connected, we can import your the rest
          of your data.
        </p>

        <div v-if="exchequerPlans.length > 0" class="w-full">
          <Button @click="importAll" class="w-full"> Import All Data </Button>

          <div v-if="inProgress" class="mt-6">
            <h2 class="text-xl font-semibold mb-4">Import Progress</h2>
            <ul class="space-y-2">
              <li
                v-for="(item, index) in progressReport"
                :key="index"
                class="flex items-center space-x-2"
              >
                <span>{{ item.task }}</span>
                <span v-if="item.status === 'completed'" class="text-green-500"
                  >Completed</span
                >
                <span
                  v-else-if="item.status === 'in-progress'"
                  class="text-blue-500"
                  >In progress...</span
                >
              </li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  </ClientOnly>
</template>

<script setup>
const { $auth, $api } = useNuxtApp();

let user = computed(() => $auth?.user || { integrations: null });

let ynabPlans = ref([]);
let exchequerPlans = ref([]);
let selectedPlans = ref([]);

let progressReport = ref([]);
let inProgress = ref(false);

async function importAll() {
  try {
    inProgress.value = true;

    let importingPayees = {
      task: "Importing Payees",
      status: "in-progress",
    };

    progressReport.value.push(importingPayees);
    await $api("/api/ynab/import/payees", {
      method: "POST",
    });
    importingPayees.status = "completed";

    let importingCategories = {
      task: "Importing Categories",
      status: "in-progress",
    };

    progressReport.value.push(importingCategories);
    await $api("/api/ynab/import/categories", {
      method: "POST",
    });
    importingCategories.status = "completed";

    let importingAccounts = {
      task: "Importing Accounts",
      status: "in-progress",
    };

    progressReport.value.push(importingAccounts);
    await $api("/api/ynab/import/accounts", {
      method: "POST",
    });
    importingAccounts.status = "completed";

    let importingTransactions = {
      task: "Importing Transactions. This one might take a while...",
      status: "in-progress",
    };

    progressReport.value.push(importingTransactions);
    await $api("/api/ynab/import/transactions", {
      method: "POST",
    });
    importingTransactions.status = "completed";

    progressReport.value.push({
      task: "Import completed successfully!",
      status: "completed",
    });

    inProgress.value = false;
    // Optionally, redirect or update the UI here
  } catch (error) {
    console.error("Error importing plans:", error);
    alert("Failed to import plans. Please try again later.");
  }
}

onMounted(async () => {
  try {
    const response = await $api("/api/plans");
    exchequerPlans.value = response || [];
  } catch (error) {
    console.error("Error fetching existing plans:", error);
  }

  if (user.value.integrations && user.value.integrations.ynab) {
    // Fetch plans from the backend
    try {
      const response = await $api("/api/ynab/plans");
      ynabPlans.value = response || [];

      if (ynabPlans.value.length === 0) {
        alert("No plans found in your YNAB account.");
      }

      if (ynabPlans.value.length === 1) {
        // Auto-select the only available plan
        selectedPlans.value = [ynabPlans.value[0].id];
      }
    } catch (error) {
      console.error("Error fetching plans:", error);
      alert("Failed to load plans. Please try again later.");
    }
  }
});
</script>
