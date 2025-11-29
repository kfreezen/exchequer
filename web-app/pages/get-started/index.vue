<template>
  <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
    <div class="mb-12">
      <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
        Getting Started
      </h1>
      <p class="text-lg text-foreground/90">
        You can't go wrong with only one plan!
      </p>
    </div>

    <div class="relative bg-muted rounded-full p-1 mb-8 max-w-xs">
      <div
        :class="`absolute top-1 bottom-1 rounded-full transition-all duration-300 ${
          billingRequested === 'annual'
            ? 'left-1 right-1/2 bg-primary shadow-glow'
            : 'left-1/2 right-1 bg-primary shadow-glow'
        }`"
      />
      <div class="relative flex">
        <button
          @click="billingRequested = 'annual'"
          :class="`flex-1 py-2 px-4 text-sm font-medium rounded-full transition-colors ${
            billingRequested === 'annual'
              ? 'text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
          }`"
        >
          Annual
        </button>
        <button
          type="button"
          @click="billingRequested = 'monthly'"
          :class="`flex-1 py-2 px-4 text-sm font-medium rounded-full transition-colors ${
            billingRequested === 'monthly'
              ? 'text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
          }`"
        >
          Monthly
        </button>
      </div>
    </div>

    <Card class="w-full max-w-xs">
      <CardContent class="flex flex-col p-6 gap-4">
        <CardTitle class="font-bold text-2xl">Professional</CardTitle>

        <p></p>
        <div>
          <p>
            <span class="font-bold text-2xl"
              >${{ pricing[billingRequested] }}
            </span>
            <span class="text-foreground/80">{{
              billingRequested === "annual"
                ? "/year billed annually"
                : "/month month-to-month"
            }}</span>
          </p>
          <p class="text-sm text-foreground/80">
            Free 14-day trial. No credit card required.
          </p>
        </div>
        <Button class="w-full" size="lg"> Get Started </Button>
      </CardContent>
    </Card>
  </main>
</template>

<script setup>
const billingRequested = ref("annual");

let pricing = {
  annual: "99",
  monthly: "9.90",
};
</script>
