<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
          Accounts
        </h1>
        <p class="text-lg text-foreground/90">
          Start accounting by importing your stuff.
        </p>
      </div>

      <div class="flex flex-col">
        <Card v-for="account in accounts" :key="account.id">
          <CardHeader
            class="text-lg font-semibold text-foreground flex flex-row items-center justify-between"
          >
            <span>
              {{ account.name }}
            </span>

            <div class="flex flex-row items-center">
              <Button variant="outline" size="sm"> Manage </Button>
              <Button variant="outline" size="sm" class="ml-2"> Delete </Button>
            </div>
          </CardHeader>
        </Card>
      </div>

      <button @click="showAddAccount()">
        <Card>
          <CardContent class="flex items-center justify-start gap-6 pt-3 pb-3">
            <Plus class="w-12 h-12 text-foreground" />
            <p class="text-foreground/70 max-w-md text-center">
              Add an account
            </p>
          </CardContent>
        </Card>
      </button>
    </main>

    <Dialog v-model:open="showAddAccountDialog">
      <DialogContent class="font-standard">
        <DialogHeader>
          <DialogTitle>Add Account</DialogTitle>
          <DialogDescription>
            Connect your account to start tracking your finances.
          </DialogDescription>
        </DialogHeader>
        <form @submit.prevent="addAccount" class="flex flex-col gap-4">
          <div class="space-y-2">
            <Label for="plan-id">Plan</Label>
            <Select id="plan-id" required v-model="newAccount.entityId">
              <SelectTrigger>
                <SelectValue placeholder="Select a plan" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="entity in entities"
                  :key="entity.id"
                  :value="entity.id"
                >
                  {{ entity.name }}
                </SelectItem>
                <SelectItem v-if="entities.length === 0" disabled>
                  No plans available
                </SelectItem>
                <SelectItem value="new-plan" @click="showPlanDialog = true">
                  <Plus class="w-4 h-4 mr-2 inline" />
                  Create a new plan
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label for="account">Account</Label>
            <Input
              id="account"
              autocomplete="off"
              type="text"
              placeholder="e.g., Checking Account"
              required
              v-model="newAccount.name"
            />
          </div>
          <!-- Form fields for adding an account go here -->
          <div class="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              @click="showAddAccountDialog = false"
            >
              Cancel
            </Button>
            <Button type="submit">Add Account</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>

    <AddPlanDialog
      v-model="showPlanDialog"
      @created="newAccount.entityId = $event.id"
    />
  </ClientOnly>
</template>

<script setup>
import { Plus } from "lucide-vue-next";
import { cn } from "@/lib/utils";

const { $auth, $api } = useNuxtApp();

const user = computed(() => $auth?.user || null);

const showAddAccountDialog = ref(false);
const showPlanDialog = ref(false);

const entities = computed(() => (user.value ? user.value.entities : []));
const accounts = computed(() => {
  if (!entities.value) return [];
  return entities.value.flatMap(
    (entity) =>
      entity.envelopes.filter((envelope) => envelope.type === "account") || [],
  );
});

// Add Account Dialog
const newAccount = ref({
  name: "",
  entityId: null,
  // Add other necessary fields here
});

function showAddAccount() {
  showAddAccountDialog.value = true;
}

async function addAccount() {
  try {
    let envelope = $api(`/entities/${newAccount.value.entityId}/envelopes`, {
      method: "POST",
      body: {
        type: "account",
        name: newAccount.value.name,
        // Add other necessary fields here
      },
    });
  } catch (error) {
    console.error("Error adding account:", error);
  }
}
</script>
