<template>
  <header
    class="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
  >
    <div
      class="container flex h-16 max-w-screen-xl items-center justify-between px-8"
    >
      <NuxtLink to="/" class="flex items-center gap-2">
        <Mail class="h-12" />
        exchequer.io
      </NuxtLink>

      <!-- Desktop Navigation -->
      <nav class="hidden md:flex items-center space-x-6 text-sm font-medium">
        <NuxtLink
          v-for="link in links"
          :key="link.path"
          :to="link.path"
          @click="mobileMenuOpen = false"
          class="transition-colors hover:text-primary text-foreground/80 py-2"
        >
          {{ link.name }}
        </NuxtLink>
      </nav>

      <!-- Mobile Menu Button -->
      <button
        @click="mobileMenuOpen = !mobileMenuOpen"
        class="md:hidden p-2 text-foreground hover:text-primary"
        aria-label="Toggle menu"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            v-if="!mobileMenuOpen"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
          <path
            v-else
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <!-- Mobile Navigation -->
    <nav
      v-if="mobileMenuOpen"
      class="md:hidden border-t border-border/40 bg-background/95 backdrop-blur"
    >
      <div class="container flex flex-col space-y-3 px-8 py-4">
        <NuxtLink
          v-for="link in links"
          :key="link.path"
          :to="link.path"
          @click="mobileMenuOpen = false"
          class="transition-colors hover:text-primary text-foreground/80 py-2"
        >
          {{ link.name }}
        </NuxtLink>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { Mail } from "lucide-vue-next";

const mobileMenuOpen = ref(false);

const links = [
  { name: "Home", path: "/" },
  { name: "Pricing", path: "/pricing" },
  { name: "About", path: "/about" },
];
</script>
