<template>
  <div class="min-h-screen flex items-center justify-center p-4 space-y-4">
    <div class="w-full max-w-md">
      <div class="flex flex-col items-center justify-center space-x-2">
        <div class="flex items-center justify-center gap-2">
          <Mail class="h-24" />
          exchequer.io
        </div>
      </div>
      <form @submit.prevent="resetPassword" class="space-y-4">
        <p class="text-muted-foreground">
          Enter the code sent to your email to reset your password.
        </p>
        <div class="space-y-2">
          <Label htmlFor="resetPassword">Reset Password Code</Label>
          <Input
            id="resetPassword"
            name="resetPassword"
            type="text"
            v-model="resetPasswordCode"
            required
          />
        </div>

        <div class="space-y-2">
          <Label htmlFor="resetPassword">New Password</Label>
          <Input
            id="newPassword"
            name="newPassword"
            type="password"
            v-model="newPassword"
            required
          />
        </div>

        <Button type="submit" class="w-full"> Reset Password </Button>

        <div class="text-center flex items-center justify-between">
          <button
            type="button"
            @click="router.push('/signin')"
            class="text-sm text-primary hover:text-foreground transition-colors"
          >
            Back to sign in.
          </button>
        </div>
      </form>
      <Card class="mt-4 overflow-hidden bg-red-100" v-if="isError">
        <CardContent class="p-4">
          <p class="text-red-600 text-sm">
            An error occurred while resetting your password. Please try again.
          </p>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { Mail } from "lucide-vue-next";

const auth = useNuxtApp().$auth;
const route = useRoute();

const resetPasswordCode = ref("");
const newPassword = ref("");
const isLoading = ref(false);
const isError = ref(false);

const resetPassword = async () => {
  if (isLoading.value) return;

  isLoading.value = true;
  isError.value = false;
  try {
    await auth.resetPassword(
      route.query.email,
      resetPasswordCode.value,
      newPassword.value,
    );
    navigateTo({
      path: "/signin",
      query: { postReset: route.query.email },
    });
  } catch (error) {
    console.error("Email resetPassword failed:", error);
    isError.value = true;
    return;
  } finally {
    isLoading.value = false;
  }
};
</script>
