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

        <!-- All Transactions Section with Inline Editing -->
        <div class="flex flex-col items-start justify-start gap-2 mt-8">
          <div class="flex items-center justify-between w-full">
            <div>
              <h2 class="text-2xl font-bold">All Transactions</h2>
              <p class="mb-4 text-foreground/70">
                Click on any field to edit. Changes are saved automatically.
              </p>
            </div>
            <Button @click="showAddForm = true" v-if="!showAddForm">
              <Plus class="w-4 h-4 mr-2" />
              Add Transaction
            </Button>
          </div>

          <!-- Add Transaction Form -->
          <div
            v-if="showAddForm"
            class="w-full p-4 border border-foreground/20 rounded-lg bg-foreground/5 mb-4"
          >
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-medium">Add Transaction</h3>
              <Button variant="ghost" size="sm" @click="closeAddForm">
                <X class="w-4 h-4" />
              </Button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1">Date</label>
                <input
                  type="date"
                  v-model="newTransaction.date"
                  class="w-full px-3 py-2 border border-foreground/20 rounded-md bg-background"
                />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1"
                  >Description</label
                >
                <input
                  type="text"
                  v-model="newTransaction.description"
                  placeholder="Enter description..."
                  class="w-full px-3 py-2 border border-foreground/20 rounded-md bg-background"
                />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Amount</label>
                <input
                  type="number"
                  step="0.01"
                  v-model="newTransaction.amount"
                  placeholder="0.00"
                  class="w-full px-3 py-2 border border-foreground/20 rounded-md bg-background"
                />
              </div>
              <div class="flex items-end">
                <Button
                  @click="addTransaction"
                  :disabled="!newTransaction.date || !newTransaction.amount"
                  class="w-full"
                >
                  Add
                </Button>
              </div>
            </div>
          </div>

          <div class="w-full overflow-x-auto">
            <table class="w-full border-collapse">
              <thead>
                <tr class="border-b border-foreground/20">
                  <th></th>
                  <th class="text-left p-2 font-medium">Date</th>
                  <th class="text-left p-2 font-medium">Payee</th>
                  <th class="text-left p-2 font-medium">Description</th>
                  <th class="text-right p-2 font-medium">Amount</th>
                  <th class="text-left p-2 font-medium">Envelope</th>
                  <th class="text-left p-2 font-medium">Entity</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(transaction, idx) in filteredAllTransactions"
                  :key="transaction.id"
                  class="border-b border-foreground/10 hover:bg-foreground/5"
                  :class="{ 'opacity-50': transaction.saving }"
                >
                  <td class="p-2">
                    <Checkbox v-model="transaction.selected" />
                  </td>
                  <td class="p-2">
                    <input
                      type="date"
                      :value="formatDateForInput(transaction.date)"
                      @change="
                        updateTransaction(
                          transaction,
                          'date',
                          $event.target.value,
                        )
                      "
                      class="bg-transparent border border-transparent hover:border-foreground/20 focus:border-foreground/40 rounded px-1 py-0.5 w-32"
                    />
                  </td>
                  <td class="p-2 text-foreground/70">
                    {{ transaction.payeeName || "-" }}
                  </td>
                  <td class="p-2">
                    <input
                      type="text"
                      :value="transaction.description || ''"
                      @blur="
                        updateTransaction(
                          transaction,
                          'description',
                          $event.target.value,
                        )
                      "
                      @keydown.enter="$event.target.blur()"
                      placeholder="Add description..."
                      class="bg-transparent border border-transparent hover:border-foreground/20 focus:border-foreground/40 rounded px-1 py-0.5 w-full"
                    />
                  </td>
                  <td class="p-2 text-right">
                    <input
                      type="number"
                      step="0.01"
                      :value="transaction.amount"
                      @blur="
                        updateTransaction(
                          transaction,
                          'amount',
                          $event.target.value,
                        )
                      "
                      @keydown.enter="$event.target.blur()"
                      class="bg-transparent border border-transparent hover:border-foreground/20 focus:border-foreground/40 rounded px-1 py-0.5 w-24 text-right"
                    />
                  </td>
                  <td class="p-2">
                    <Select
                      :modelValue="transaction.envelopeId"
                      @update:modelValue="
                        updateTransaction(transaction, 'envelopeId', $event)
                      "
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem
                          v-for="env in allEnvelopes"
                          :key="env.id"
                          :value="env.id"
                        >
                          {{ env.name }}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </td>
                  <td class="p-2">
                    <select
                      :value="transaction.entityId || ''"
                      @change="
                        updateTransaction(
                          transaction,
                          'entityId',
                          $event.target.value,
                        )
                      "
                      class="bg-transparent border border-transparent hover:border-foreground/20 focus:border-foreground/40 rounded px-1 py-0.5"
                      :class="{ 'text-amber-500': !transaction.entityId }"
                    >
                      <option value="" disabled>Unassigned</option>
                      <option
                        v-for="entity in entities"
                        :key="entity.id"
                        :value="entity.id"
                      >
                        {{ entity.name }}
                      </option>
                    </select>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
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

    <Card
      class="fixed bottom-4 left-4 right-4 w-80 items-center flex justify-center z-50"
      v-if="selectedAllTransactions.length > 0"
    >
      <CardContent class="flex flex-col items-start gap-4 p-4 w-80">
        <div>
          Amount:
          {{
            selectedAllTransactions
              .reduce((sum, tx) => Number(sum) + Number(tx.amount), 0)
              .toFixed(2)
          }}
        </div>
      </CardContent>
    </Card>
  </ClientOnly>
</template>

<script setup>
import { Check, Plus, X } from "lucide-vue-next";

const { $auth, $api } = useNuxtApp();

const allTransactions = ref([]);
const unassignedTransactions = ref([]);
const allEnvelopes = ref([]);
const searchQuery = ref("");
const showAddForm = ref(false);
const newTransaction = ref({
  date: new Date().toISOString().split("T")[0],
  description: "",
  amount: null,
  approved: true,
});

const filteredUnassignedTransactions = computed(() => {
  if (!searchQuery.value) return unassignedTransactions.value;

  return unassignedTransactions.value.filter((tx) =>
    tx.payeeName
      ?.toLowerCase()
      .includes(searchQuery.value.trim().toLowerCase()),
  );
});

const filteredAllTransactions = computed(() => {
  if (!searchQuery.value) return allTransactions.value;

  const query = searchQuery.value.trim().toLowerCase();
  return allTransactions.value.filter(
    (tx) =>
      tx.payeeName?.toLowerCase().includes(query) ||
      tx.description?.toLowerCase().includes(query),
  );
});

const selectedAllTransactions = computed(() =>
  filteredAllTransactions.value.filter((tx) => tx.selected),
);

const envelope = ref(null);

const selectedEntity = ref(null);

const user = computed(() => $auth && $auth.user);
const entities = computed(() => user.value?.entities || []);

const lastIndex = ref(null);
const selectedTransactions = computed(() =>
  unassignedTransactions.value.filter((tx) => tx.selected),
);

function formatDateForInput(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toISOString().split("T")[0];
}

function selectTransaction(transaction, index, event, noToggle) {
  if (!noToggle) transaction.selected = !transaction.selected;
  if (!event.shiftKey) {
    lastIndex.value = index;
    return;
  }

  if (event.shiftKey && lastIndex.value !== null) {
    const start = Math.min(lastIndex.value, index);
    const end = Math.max(lastIndex.value, index);

    for (let i = start; i <= end; i++) {
      filteredUnassignedTransactions.value[i].selected = true;
    }
  }
}

async function updateTransaction(transaction, field, value) {
  // Skip if value hasn't changed
  const currentValue = transaction[field];
  if (String(currentValue || "") === String(value || "")) return;

  transaction.saving = true;

  const body = {};
  if (field === "amount") {
    body.amount = parseFloat(value);
  } else if (field === "date") {
    body.date = value;
  } else if (field === "description") {
    body.description = value;
  } else if (field === "envelopeId") {
    body.envelopeId = value;
  } else if (field === "entityId") {
    body.entityId = value;
  }

  try {
    const updated = await $api(`/transactions/${transaction.id}`, {
      method: "PUT",
      body,
    });

    // Update the transaction in our list
    Object.assign(transaction, updated);
    transaction.amount = Number(updated.amount);

    // If envelope changed, remove from this view
    if (field === "envelopeId" && value !== envelope.value.id) {
      allTransactions.value = allTransactions.value.filter(
        (tx) => tx.id !== transaction.id,
      );
      unassignedTransactions.value = unassignedTransactions.value.filter(
        (tx) => tx.id !== transaction.id,
      );
    }

    // If entity was assigned, remove from unassigned list
    if (field === "entityId" && value) {
      unassignedTransactions.value = unassignedTransactions.value.filter(
        (tx) => tx.id !== transaction.id,
      );
    }
  } catch (error) {
    console.error("Failed to update transaction:", error);
  } finally {
    transaction.saving = false;
  }
}

function setEnvelopeData(data) {
  for (const tx of data.transactions) {
    tx.amount = Number(tx.amount);
    tx.saving = false;
  }

  envelope.value = data;
  allTransactions.value = data.transactions.map((tx) => ({ ...tx }));
  unassignedTransactions.value = data.transactions
    .filter((tx) => !tx.entityId)
    .map((tx) => ({ ...tx, selected: false }));
}

function setEnvelopeTransactions(data) {
  for (const tx of data) {
    tx.amount = Number(tx.amount);
    tx.saving = false;
  }

  envelope.value.transactions = data;
  allTransactions.value = data.map((tx) => ({ ...tx }));
  unassignedTransactions.value = data
    .filter((tx) => !tx.entityId)
    .map((tx) => ({ ...tx, selected: false }));
}

function closeAddForm() {
  showAddForm.value = false;
  newTransaction.value = {
    date: new Date().toISOString().split("T")[0],
    description: "",
    amount: null,
    approved: true,
  };
}

async function addTransaction() {
  if (!newTransaction.value.date || !newTransaction.value.amount) return;

  try {
    const created = await $api("/transactions", {
      method: "POST",
      body: {
        date: newTransaction.value.date,
        description: newTransaction.value.description || null,
        amount: parseFloat(newTransaction.value.amount),
        approved: newTransaction.value.approved,
        envelopeId: envelope.value.id,
      },
    });

    // Add to the transactions list
    created.amount = Number(created.amount);
    created.saving = false;
    allTransactions.value.unshift({ ...created });
    if (!created.entityId) {
      unassignedTransactions.value.unshift({ ...created, selected: false });
    }

    closeAddForm();
  } catch (error) {
    console.error("Failed to create transaction:", error);
  }
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

  // Fetch envelope data and all envelopes in parallel
  const [envelopeData, envelopes] = await Promise.all([
    $api(`/envelopes/${envelopeId}`),
    $api("/envelopes"),
  ]);

  setEnvelopeData(envelopeData);
  allEnvelopes.value = envelopes;
});
</script>
