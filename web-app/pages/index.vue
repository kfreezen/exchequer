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
        class="flex flex-col items-center justify-center gap-6"
        v-if="user && user.entities.length === 0"
      >
        <Mail class="w-16 h-16 text-foreground" />
        <h2 class="text-2xl font-semibold text-foreground/70">
          Click here to set up your dashboard
        </h2>
        <p class="text-foreground/70 max-w-md text-center">
          Or you can set things up manually by adding your personal plan and any
          business entities you want to track.
        </p>
      </div>
    </main>
  </ClientOnly>
</template>

<script setup>
import { Mail } from "lucide-vue-next";

const { $auth } = useNuxtApp();

const user = computed(() => $auth && $auth.user);
</script>
