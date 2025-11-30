<template>
  <SidebarProvider>
    <AppSidebar />
    <div class="font-standard flex-1">
      <NuxtRouteAnnouncer />
      <main class="flex-1">
        <NuxtPage />
      </main>
    </div>
  </SidebarProvider>
  <Dialog v-model:open="showGlobalDialog">
    <DialogContent class="max-w-2xl font-standard">
      <DialogHeader>
        <DialogTitle>{{ globalDialog.title }}</DialogTitle>
      </DialogHeader>
      <div class="p-4">
        <component :is="globalDialog.component" v-bind="globalDialog.props" />
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup>
let showGlobalDialog = ref(false);
let globalDialog = useGlobalDialog().dialogState;
</script>
