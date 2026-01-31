<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
          Envelope Details
        </h1>
        <p class="mt-4 text-lg text-foreground/70">
          {{ envelope?.name || "Loading..." }}
        </p>
      </div>
      <div class="flex flex-col gap-6" @selectstart.prevent>
        <Input v-model="searchQuery" placeholder="Search transactions..." />

        <div
          class="flex flex-col items-start justify-start gap-2"
          v-if="unassignedTransactions.length > 0"
        >
          <h2 class="text-2xl font-bold">Unassigned Transactions</h2>
          <p class="mb-4">
            You've got some transactions that need to be assigned a tax
            classification.
          </p>

          <div
            v-for="(transaction, idx) in filteredUnassignedTransactions"
            :key="transaction.id"
            class="p-2 border border-foreground/10 rounded-md w-full flex items-center gap-4 cursor-pointer"
            :class="{ 'bg-foreground/5': transaction.selected }"
            @click="selectTransaction(transaction, idx, $event)"
          >
            <Checkbox
              v-model="transaction.selected"
              @click.stop="selectTransaction(transaction, idx, $event, true)"
            />
            {{ transaction.payeeName }} | {{ transaction.amount }}
          </div>
        </div>
        <div v-else class="flex flex-col">
          <h2 class="text-2xl font-bold">
            All transactions have a tax classification
          </h2>
        </div>
      </div>
      <div class="h-32"></div>

      <Card
        v-if="selectedTransactions.length > 0"
        class="fixed bottom-16 left-4 right-4 w-80 items-center flex justify-center z-50"
      >
        <CardContent class="flex flex-col items-start gap-4 p-4 w-80">
          <h3 class="text-lg font-medium">
            Assign {{ selectedTransactions.length }} Transactions To:
          </h3>
          <div class="flex items-center gap-2 w-full">
            <Select v-model="selectedEntity">
              <SelectTrigger ref="planNameRef" class="w-full">
                <SelectValue placeholder="Business or Personal?" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="entity in user.entities"
                  :key="entity.id"
                  :value="entity.id"
                >
                  {{ entity.name }}
                </SelectItem>
              </SelectContent>
            </Select>
            <Button @click="assignTransactionsToEntity()">
              <Check class="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  </ClientOnly>
</template>

<script setup>
import { Check } from "lucide-vue-next";

const { $auth, $api } = useNuxtApp();

const unassignedTransactions = ref([]);
const searchQuery = ref("");
const filteredUnassignedTransactions = computed(() => {
  if (!searchQuery.value) return unassignedTransactions.value;

  return unassignedTransactions.value.filter((tx) =>
    tx.payeeName.toLowerCase().includes(searchQuery.value.trim().toLowerCase()),
  );
});
const envelope = ref(null);

const selectedEntity = ref(null);

const user = computed(() => $auth && $auth.user);

const lastIndex = ref(null);
const selectedTransactions = computed(() =>
  unassignedTransactions.value.filter((tx) => tx.selected),
);

function selectTransaction(transaction, index, event, noToggle) {
  console.log("event", event);

  if (!noToggle) transaction.selected = !transaction.selected;
  if (!event.shiftKey) {
    lastIndex.value = index;
    return;
  }

  console.log("lastIndex", lastIndex.value, "index", index);

  if (event.shiftKey && lastIndex.value !== null) {
    const start = Math.min(lastIndex.value, index);
    const end = Math.max(lastIndex.value, index);

    for (let i = start; i <= end; i++) {
      filteredUnassignedTransactions.value[i].selected = true;
    }
  }
}
function setEnvelopeData(data) {
  for (const tx of data.transactions) {
    tx.amount = Number(tx.amount);
  }

  envelope.value = data;
  unassignedTransactions.value = data.transactions
    .filter((tx) => !tx.entityId)
    .map((tx) => ({ ...tx, selected: false }));

  console.log("unassignedTransactions", unassignedTransactions.value.length);
}

function setEnvelopeTransactions(data) {
  for (const tx of data) {
    tx.amount = Number(tx.amount);
  }

  envelope.value.transactions = data;
  unassignedTransactions.value = data
    .filter((tx) => !tx.entityId)
    .map((tx) => ({ ...tx, selected: false }));
}

async function assignTransactionsToEntity() {
  const entityId = selectedEntity.value;
  if (!entityId) return;

  let transactions = await $api(
    `/envelopes/${envelope.value.id}/assign-transactions`,
    {
      method: "POST",
      body: {
        entityId,
        transactionIds: selectedTransactions.value.map((t) => t.id),
      },
    },
  );

  setEnvelopeTransactions(transactions);
  selectedEntity.value = null;
}

onMounted(async () => {
  const route = useRoute();
  const envelopeId = route.params.envelopeId;

  setEnvelopeData(await $api(`/envelopes/${envelopeId}`));
});
</script>
