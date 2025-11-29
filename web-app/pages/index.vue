<template>
  <!-- Hero Section -->
  <section class="py-16 md:py-24 px-8">
    <div class="container max-w-screen-xl mx-auto">
      <div class="grid md:grid-cols-2 gap-12 items-center">
        <div class="space-y-6">
          <h1
            class="text-4xl md:text-5xl lg:text-6xl font-bold font-roboto-slab text-foreground leading-tight"
          >
            Business and Personal Finance, All in One Place
          </h1>
          <p class="text-lg md:text-xl text-muted-foreground">
            You there! Are you one of the ten million people that has to track
            both business and personal finances? This app combines the power of
            envelope finance management with business expense tracking.
          </p>

          <div class="flex flex-col sm:flex-row gap-4 pt-4">
            <Button @click="console.log('hello')">Get Started</Button>
          </div>
        </div>
        <div class="flex justify-center">
          <div
            class="relative w-full max-w-md aspect-square rounded-3xl p-8 flex items-center justify-center"
          ></div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Mail } from "lucide-vue-next";
</script>
