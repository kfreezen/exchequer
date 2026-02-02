<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
          Envelopes
        </h1>
        <p class="mt-4 text-lg text-foreground/70">
          Manage your budget envelopes and view transactions.
        </p>
      </div>

      <div class="flex flex-col gap-4">
        <Input v-model="searchQuery" placeholder="Search envelopes..." />

        <div v-if="loading" class="text-foreground/70">Loading envelopes...</div>

        <div v-else-if="filteredEnvelopes.length === 0" class="text-foreground/70">
          No envelopes found.
        </div>

        <div v-else class="flex flex-col gap-2">
          <NuxtLink
            v-for="envelope in filteredEnvelopes"
            :key="envelope.id"
            :to="`/envelopes/${envelope.id}`"
            class="p-4 border border-foreground/10 rounded-md hover:bg-foreground/5 active:bg-foreground/10 transition-colors flex items-center justify-between"
          >
            <div class="flex flex-col">
              <span class="font-medium">{{ envelope.name }}</span>
              <span
                v-if="envelope.entityId"
                class="text-sm text-foreground/50"
              >
                Assigned
              </span>
              <span v-else class="text-sm text-amber-500">Unassigned</span>
            </div>
            <ChevronRight class="w-5 h-5 text-foreground/50" />
          </NuxtLink>
        </div>
      </div>
    </main>
  </ClientOnly>
</template>

<script setup>
import { ChevronRight } from "lucide-vue-next";

const { $api } = useNuxtApp();

const envelopes = ref([]);
const loading = ref(true);
const searchQuery = ref("");

const filteredEnvelopes = computed(() => {
  if (!searchQuery.value) return envelopes.value;

  const query = searchQuery.value.trim().toLowerCase();
  return envelopes.value.filter((envelope) =>
    envelope.name.toLowerCase().includes(query),
  );
});

onMounted(async () => {
  try {
    envelopes.value = await $api("/envelopes");
  } catch (error) {
    console.error("Failed to load envelopes:", error);
  } finally {
    loading.value = false;
  }
});
</script>
