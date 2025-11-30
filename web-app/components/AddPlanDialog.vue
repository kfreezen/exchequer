<template>
  <Dialog :open="modelValue" @update:open="emit('update:modelValue', $event)">
    <DialogContent class="max-w-2xl font-standard">
      <DialogHeader>
        <DialogTitle>Add a New Plan</DialogTitle>
      </DialogHeader>
      <div class="p-4">
        <form @submit.prevent="createPlan" class="flex flex-col gap-4">
          <div class="space-y-2">
            <Label for="plan-type">Plan Type</Label>
            <Select
              id="plan-type"
              v-model="newPlan.type"
              required
              @update:modelValue="onPlanTypeChange"
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a plan type" />
              </SelectTrigger>
              <SelectContent class="font-standard">
                <SelectItem value="personal">Personal</SelectItem>
                <SelectItem value="business">Business</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label for="plan-name">Plan Name</Label>
            <Input
              id="plan-name"
              v-model="newPlan.name"
              type="text"
              required
              ref="planNameRef"
            />
          </div>
          <div class="flex justify-end mt-4">
            <Button
              variant="ghost"
              @click="emit('update:modelValue', false)"
              type="button"
            >
              Cancel
            </Button>
            <Button type="submit">Create Plan</Button>
          </div>
        </form>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup>
let props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue", "created"]);

const newPlan = ref({
  name: "",
  type: null,
});

const { $auth, $api } = useNuxtApp();

const user = computed(() => $auth && $auth.user);

async function createPlan() {
  // Logic to create a new plan goes here
  try {
    let created = await $api("/entities", {
      method: "POST",
      body: {
        name: newPlan.value.name,
        type: newPlan.value.type,
      },
    });

    user.value.entities.push(created);
    newPlan.value = {
      name: "",
      type: null,
    };

    emit("created", created);
    emit("update:modelValue", false);
  } catch (error) {
    console.error("Error creating plan:", error);
  }
}

function onPlanTypeChange(value) {
  if (user.value.entities.filter((e) => e.type === value).length === 0) {
    newPlan.value.name = value === "personal" ? "Personal" : "Business";
  }
}
</script>
