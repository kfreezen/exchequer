<template>
  <div
    class="flex items-center gap-4 p-4 h-14 rounded-full border-2 cursor-pointer transition-all duration-200"
    :class="
      active
        ? 'border-primary bg-primary'
        : 'border hover:border-primary hover:bg-primary/1'
    "
    @click="emit('select')"
  >
    <div
      class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-200"
    >
      <Check v-if="active" class="w-4 h-4 text-primary-foreground" />
    </div>
    <span
      class="font-medium flex-1"
      :class="active ? 'text-primary-foreground' : 'text-foreground'"
    >
      {{ description || "" }}
    </span>
  </div>
</template>
<script setup>
import { Check } from "lucide-vue-next";

let props = defineProps({
  active: {
    type: Boolean,
    required: true,
  },
  description: {
    type: String,
    required: false,
    default: "",
  },
});

const emit = defineEmits(["select"]);
</script>
