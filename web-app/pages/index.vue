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
              <Mail class="w-16 h-16 text-foreground" />
              <h2 class="text-2xl font-semibold text-foreground/70">
                Click here to set up your dashboard
              </h2>
              <p class="text-foreground/70 max-w-md text-center">
                Let us take the headache out of getting started.
              </p>
            </CardContent>
          </Card>
        </button>

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
        </button>
      </div>
      <div v-else class="flex flex-col gap-6">
        <div class="flex flex-col items-start justify-start">
          <h2 class="text-2xl font-bold">Accounts</h2>
          <div v-for="account in accounts" :key="account.id">
            {{ account.name }}
          </div>
          <NuxtLink to="/accounts">
            <Button> Add accounts to get started </Button>
          </NuxtLink>
        </div>

        <div class="flex flex-col items-start justify-start">
          <h2 class="text-2xl font-bold">Envelopes</h2>
          <div v-for="envelope in envelopes" :key="envelope.id">
            {{ envelope.name }}
          </div>
          <Button @click="addEnvelopes()" v-if="accounts.length > 0">
            Add envelopes to get started
          </Button>
          <p v-else class="text-foreground/70">
            Please add at least one account before adding envelopes.
          </p>
        </div>
      </div>
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
  </ClientOnly>
</template>

<script setup>
import { Mail, Plus } from "lucide-vue-next";

const { $auth, $api } = useNuxtApp();

const user = computed(() => $auth && $auth.user);
let accounts = computed(() => {
  let accumulated = [];

  let entities = user.value ? user.value.entities || [] : [];
  if (entities.length === 0) return [];

  for (let entity of entities) {
    let accounts = entity.envelopes.filter((acc) => acc.type === "account");
    accumulated = accumulated.concat(accounts);
  }

  return accumulated;
});
const planNameRef = useTemplateRef("planNameRef");

const showPlanDialog = ref(false);
const showAccountDialog = ref(false);
const showEnvelopeDialog = ref(false);

function addPlan() {
  showPlanDialog.value = true;
}
</script>
