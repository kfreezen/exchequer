<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
          Dashboard
        </h1>
        <p class="text-lg text-foreground/90">Where the magic happens.</p>
      </div>

      <div
        v-if="user && user.entities.length === 0"
        class="flex flex-col items-center gap-6 max-w-lg"
      >
        <button @click="setup()" v-if="user && user.entities.length === 0">
          <Card>
            <CardContent
              class="flex flex-col items-center justify-center gap-6 p-6"
            >
              <Mail class="w-16 h-16 taext-foreground" />
              <h2 class="text-2xl font-semibold text-foreground/70">
                Click here to set up your dashboard
              </h2>
              <p class="text-foreground/70 max-w-md text-center">
                Let us take the headache out of getting started.
              </p>
            </CardContent>
          </Card>
        </button>

        <!--
        <div>or</div>

        <button @click="addPlan()" v-if="user && user.entities.length === 0">
          <Card>
            <CardContent
              class="flex items-center justify-start gap-6 pt-3 pb-3"
            >
              <Plus class="w-12 h-12 text-foreground" />
              <p class="text-foreground/70 max-w-md text-center">Add a plan</p>
            </CardContent>
          </Card>
        </button>-->
      </div>
      <div v-else class="flex flex-col gap-6">
        <div
          class="flex flex-col items-start justify-start gap-2"
          v-if="unassignedEnvelopes.length > 0"
        >
          <h2 class="text-2xl font-bold">Unassigned Envelopes</h2>
          <p class="mb-4">
            The whole goal here is to assign these envelopes a home. Select some
            and then tell us whether they are for personal or business use.
          </p>

          <div
            v-for="envelope in unassignedEnvelopes"
            :key="envelope.id"
            class="p-2 border border-foreground/10 rounded-md w-full flex items-center gap-4 cursor-pointer"
            :class="{ 'bg-foreground/5': envelope.selected }"
            @click="envelope.selected = !envelope.selected"
          >
            <Checkbox v-model="envelope.selected" @click.stop="null" />
            {{ envelope.name }}
          </div>
        </div>
        <div v-else class="flex flex-col">
          <h2
            v-if="unassignedTransactionEnvelopes.length === 0"
            class="text-2xl font-bold flex gap-4"
          >
            <Check class="w-8 h-8" /> All envelopes have a tax classification
          </h2>
        </div>

        <div
          v-if="unassignedEnvelopes.length === 0"
          class="flex flex-col items-start justify-start gap-2"
        >
          <h2
            class="text-2xl font-bold"
            v-if="unassignedTransactionEnvelopes.length > 0"
          >
            Envelopes with unassigned transactions
          </h2>
          <p class="mb-4" v-if="unassignedTransactionEnvelopes.length > 0">
            Some envelopes have transactions that need to be assigned a tax
            classification. Select the envelopes below and then tell us whether
            the transactions are for personal or business use.
          </p>
          <div
            v-for="envelope in unassignedTransactionEnvelopes"
            :key="envelope.id"
            class="p-2 hover:bg-foreground/5 active:bg-foreground/10 border border-foreground/10 rounded-md w-full flex items-center gap-4 cursor-pointer flex flex-row justify-between"
            @click="envelope.selected = !envelope.selected"
          >
            <div class="flex items-center gap-4">
              <Checkbox v-model="envelope.selected" @click.stop="null" />
              {{ envelope.name }} ({{ envelope.unassignedTransactionCount }}
              unassigned)
            </div>

            <Button
              @click.stop="navigateTo(`/envelopes/${envelope.id}`)"
              size="icon-sm"
            >
              <Search class="w-4 h-4" />
            </Button>
          </div>

          <h2
            v-if="unassignedTransactionEnvelopes.length === 0"
            class="text-2xl font-bold flex gap-4"
          >
            <Check class="w-8 h-8" /> All transactions have a tax classification
          </h2>
        </div>
      </div>
      <div class="h-32"></div>
    </main>

    <AddPlanDialog v-model="showPlanDialog" />

    <Dialog v-model="showEnvelopeDialog">
      <DialogContent class="max-w-2xl font-standard">
        <DialogHeader>
          <DialogTitle>Add a New Envelope</DialogTitle>
        </DialogHeader>
        <div class="p-4"></div>
      </DialogContent>
    </Dialog>

    <Card
      v-if="selectedEnvelopes.length > 0"
      class="fixed bottom-16 left-4 right-4 w-80 items-center flex justify-center z-50"
    >
      <CardContent class="flex flex-col items-start gap-4 p-4 w-80">
        <h3 class="text-lg font-medium">
          Assign {{ selectedEnvelopes.length }} Envelopes To:
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
          <Button @click="assignEnvelopesToEntity()">
            <Check class="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>

    <Card
      v-if="selectedTransactionEnvelopes.length > 0"
      class="fixed bottom-16 left-4 right-4 w-80 items-center flex justify-center z-50"
    >
      <CardContent class="flex flex-col items-start gap-4 p-4 w-80">
        <h3 class="text-lg font-medium">
          Assign transactions in
          {{ selectedTransactionEnvelopes.length }} envelope to:
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
          <Button @click="assignEnvelopeTransactionsToEntity()">
            <Check class="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  </ClientOnly>
</template>

<script setup>
import { Mail, Plus, Check, Search } from "lucide-vue-next";

const { $auth, $api } = useNuxtApp();

const user = computed(() => $auth && $auth.user);
const planNameRef = useTemplateRef("planNameRef");

const showPlanDialog = ref(false);
const showAccountDialog = ref(false);
const showEnvelopeDialog = ref(false);

const unassignedEnvelopes = ref([]);
const unassignedTransactionEnvelopes = ref([]);

const selectedEnvelopes = computed(() =>
  unassignedEnvelopes.value.filter((envelope) => envelope.selected),
);
const selectedEntity = ref(null);
const selectedTransactionEnvelopes = computed(() =>
  unassignedTransactionEnvelopes.value.filter((envelope) => envelope.selected),
);

function addPlan() {
  showPlanDialog.value = true;
}

async function assignEnvelopesToEntity() {
  const entityId = selectedEntity.value;
  if (!entityId) return;

  let unassigned = await $api(`/envelopes/assign`, {
    method: "POST",
    body: { entityId, envelopeIds: selectedEnvelopes.value.map((e) => e.id) },
  });

  unassignedEnvelopes.value = unassigned;
  selectedEntity.value = null;
}

async function assignEnvelopeTransactionsToEntity() {
  const entityId = selectedEntity.value;
  if (!entityId) return;

  let unassigned = await $api(`/envelopes/assign-transactions`, {
    method: "POST",
    body: {
      entityId,
      envelopeIds: selectedTransactionEnvelopes.value.map((e) => e.id),
    },
  });
  unassignedTransactionEnvelopes.value = unassigned;
  selectedEntity.value = null;
}

function setup() {
  navigateTo("/setup");
}

onMounted(async () => {
  if (user.value) {
    unassignedEnvelopes.value = await $api("/envelopes/unassigned");
    unassignedTransactionEnvelopes.value = await $api(
      "/envelopes/unassigned-transactions",
    );
  }
});
</script>
