<template>
  <div class="min-h-screen flex items-center justify-center p-4 space-y-4">
    <div class="w-full max-w-md">
      <div class="flex flex-col items-center justify-center space-x-2">
        <div class="flex items-center justify-center gap-2">
          <Mail class="h-24" />
          exchequer.io
        </div>
      </div>
      <form @submit.prevent="submit" class="space-y-4">
        <p class="text-muted-foreground">
          Enter your email and we'll send you a reset code.
        </p>
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

        <Button type="submit" class="w-full" :disabled="isLoading">
          {{ isLoading ? "Sending" : "Send a Code" }}
        </Button>

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
    </div>
  </div>
</template>
<script setup>
import { ref } from "vue";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "vue-router";

import { Mail } from "lucide-vue-next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

let auth = useAuthStore();
let router = useRouter();

let valid = ref();

let email = ref();
let password = ref();

let error = ref();

let isLoading = ref(false);

async function submit() {
  try {
    isLoading.value = true;
    await beginSubmitPasswordReset(email.value);
  } catch (error) {
    console.error(error);
  } finally {
    isLoading.value = false;
  }
}

function navigateToSignUp() {
  navigateTo({ path: "/signup" });
}

async function beginSubmitPasswordReset() {
  try {
    await auth.beginResetPassword(email.value);
    navigateTo({
      path: "/reset-password",
      query: { email: email.value },
    });
  } catch (e) {
    console.error(e);
  }
}
</script>
