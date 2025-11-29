<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md shadow-soft">
      <div class="flex flex-col items-center justify-center space-x-2">
        <div class="flex items-center justify-center gap-2">
          <Mail class="h-24" />
          exchequer.io
        </div>
      </div>

      <form @submit.prevent="verifyEmail" class="space-y-4">
        <p class="text-muted-foreground">
          Enter the verification code sent to your email to verify your account.
        </p>
        <div class="space-y-2">
          <Label htmlFor="verification">Verification Code</Label>
          <Input
            id="verification"
            name="verification"
            type="text"
            v-model="verificationCode"
            required
          />
        </div>

        <Button type="submit" class="w-full"> Verify Email </Button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { Mail } from "lucide-vue-next";

const { $api, $auth } = useNuxtApp();

if ($auth) {
  console.log("auth", await $auth.getUser());
}

const route = useRoute();

const verificationCode = ref("");
const verifyEmail = async () => {
  let auth = $auth;

  try {
    let data = await $api(`/users/${auth.user.id}/verify`, {
      method: "POST",
      body: { code: verificationCode.value },
    });

    navigateTo("/setup");
  } catch (error) {
    console.error("Email verification failed:", error);
  }
};
</script>
