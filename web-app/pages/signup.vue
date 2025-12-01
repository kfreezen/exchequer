<template>
  <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
    <div class="mb-12">
      <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
        Get Started
      </h1>
      <p class="text-lg text-foreground/90">
        Thanks for getting here, let's get an account set up first.
      </p>
    </div>

    <div>
      <form @submit.prevent="submit" class="space-y-4">
        <div class="space-y-2">
          <Label htmlFor="name">Name (so we know what to call you)</Label>
          <Input
            id="name"
            name="name"
            type="name"
            v-model="name"
            required
            placeholder="Enter your full name (or whatever you want)"
          />
        </div>
        <div class="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            name="email"
            type="email"
            v-model="email"
            required
            placeholder="Enter your email address"
          />
        </div>

        <div class="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            name="password"
            type="password"
            ref="passwordInput"
            v-model="password"
            required
            placeholder="Enter your password"
          />
        </div>

        <Card class="mb-4 pt-4 overflow-hidden bg-red-100" v-if="error">
          <CardContent>
            <p class="text-red-700">
              {{ error }}
            </p>
          </CardContent>
        </Card>

        <Button type="submit" class="w-full" :disabled="isLoading">
          {{ isLoading ? "Creating Account..." : "Create Account" }}
        </Button>

        <div class="text-center flex items-center justify-between">
          <button
            type="button"
            @click="navigateToSignIn()"
            class="text-sm text-primary hover:text-foreground transition-colors"
          >
            Already have an account? Sign in
          </button>
        </div>

        <!--
        <div
          id="appleid-signin"
          class="w-[210px] h-[40px]"
          data-color="black"
          data-border="true"
          data-type="sign-up"
></div>-->

        <!--<GoogleSignInButton text="signup_with" @success="onGoogleSignIn" />-->
      </form>
    </div>
  </main>
</template>

<script setup>
let isLoading = ref(false);
let error = ref(null);

let name = ref("");
let email = ref("");
let password = ref("");

let { $api, $auth } = useNuxtApp();
let route = useRoute();

async function submit() {
  try {
    isLoading.value = true;
    let res = await $api("/users", {
      method: "POST",
      body: {
        name: name.value,
        email: email.value,
        password: password.value,
        subscription: route.query.subscription || "professional",
        billingPeriod: route.query.billingPeriod || "annual",
        promo: false,
      },
    });

    if (res) {
      $auth.token = res.access_token;
      $auth.refreshToken = res.refresh_token;
      $auth.user = await res.user;

      navigateTo(`/verification`);
    } else {
      navigateTo("/signin");
    }
  } catch (exc) {
    console.error(exc);
    if (exc.status === 409) {
      error.value = "An account with this email already exists.";
    } else {
      error.value =
        exc?.response?.detail || "An error occurred during sign up.";
    }
  } finally {
    isLoading.value = false;
  }
}
</script>
