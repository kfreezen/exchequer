<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
          Reports
        </h1>
        <p class="text-lg text-foreground/90">Get the details here.</p>

        <div class="mt-6">
          <Button @click="navigateTo('/reports/profit-and-loss')">
            Profit and Loss Report
          </Button>
        </div>
      </div>
    </main>
  </ClientOnly>
</template>

<script setup></script>
