<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1
          class="flex flex-row items-center gap-4 text-4xl md:text-5xl font-display font-bold text-foreground"
        >
          <span> Connect your YNAB Account </span>
          <img
            src="https://api.ynab.com/papi/works_with_ynab.svg"
            alt="Works with YNAB"
            class="h-12"
          />
        </h1>
      </div>

      <div class="flex flex-col items-start gap-6 max-w-lg">
        <div class="flex flex-col gap-2">
          <SelectorItem
            :active="connectMethod == 'personalAccessToken'"
            description="Personal Access Token (complicated, we don't recommend)"
            @select="connectMethod = 'personalAccessToken'"
          />
          <SelectorItem
            :active="connectMethod == 'oauth'"
            description="OAuth (recommended)"
            @select="connectMethod = 'oauth'"
          />
        </div>
      </div>
      <div class="mt-8 w-full max-w-lg">
        <NuxtLink v-if="connectMethod == 'oauth'" to="/auth/ynab">
          <Button class="w-full"> Connect your YNAB account </Button>
        </NuxtLink>
        <div v-else class="flex flex-col gap-4">
          <p class="text-lg">
            To connect using a Personal Access Token, generate one in your YNAB
            developer settings.
          </p>
          <a href="https://app.ynab.com/settings/developer" target="_blank">
            <Button class="w-full"> YNAB Developer Settings </Button>
          </a>

          <p class="text-lg">
            Once you have your token, come back here and paste it into the form
            below.
          </p>
          <form @submit.prevent="submitToken" class="flex flex-col gap-4">
            <Input
              v-model="personalAccessToken"
              type="text"
              placeholder="Enter your Personal Access Token"
              required
            />
            <Button type="submit" class="w-full">
              Connect with Personal Access Token
            </Button>
          </form>
        </div>
      </div>
    </main>
  </ClientOnly>
</template>
<script setup>
let connectMethod = ref("oauth");

let personalAccessToken = ref("");

let { $api } = useNuxtApp();

async function submitToken() {
  try {
    // Call your backend API to connect using the personal access token
    await $api("/users/me/integrations/ynab", {
      method: "POST",
      body: {
        token: personalAccessToken.value,
      },
    });
    alert("Successfully connected to YNAB!");
  } catch (error) {
    console.error("Error connecting to YNAB:", error);
    alert("Failed to connect to YNAB. Please check your token and try again.");
  }
}
</script>
