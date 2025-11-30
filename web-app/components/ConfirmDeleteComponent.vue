<template>
  <div>
    <p>{{ description }}</p>
    <button @click="confirmDelete">Yes, Delete</button>
    <button @click="cancelDelete">Cancel</button>
  </div>
</template>
<script setup>
let props = defineProps({
  description: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["confirm", "cancel"]);
function confirmDelete() {
  emit("confirm");
}
function cancelDelete() {
  emit("cancel");
}
</script>
