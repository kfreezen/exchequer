<template>
  <div class="min-h-screen flex items-center justify-center p-4 space-y-4">
    <div class="w-full max-w-md">
      <div class="flex flex-col items-center justify-center space-x-2">
        <div class="flex items-center justify-center space-x-2">
          <img src="@/assets/images/logo.svg" alt="Stanza" class="w-48 h-24" />
        </div>
        <h2 class="text-2xl font-roboto-slab font-bold mb-4">
          The Gospel Sheet Music App
        </h2>

        <Card
          class="mb-4 overflow-hidden bg-green-100"
          v-if="route.query.postReset"
        >
          <CardContent class="p-4">
            <p class="text-green-700">
              Your password has been reset successfully. Please sign in with
              your new password.
            </p>
          </CardContent>
        </Card>
      </div>
      <form @submit.prevent="submit" class="space-y-4">
        <p class="text-muted-foreground" v-if="!route.query.redeem">
          Sign in to your account
        </p>
        <p class="text-muted-foreground" v-else>
          Sign in to redeem your gift subscription
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

        <Card class="mb-4 overflow-hidden bg-red-100" v-if="error">
          <CardContent>
            <p class="text-red-700">
              {{ error }}
            </p>
          </CardContent>
        </Card>

        <Button type="submit" class="w-full" :disabled="isLoading">
          {{ isLoading ? "Signing In..." : "Sign In" }}
        </Button>

        <div class="text-center flex items-center justify-between">
          <button
            type="button"
            @click="navigateToSignUp"
            class="text-sm text-primary hover:text-foreground transition-colors"
          >
            Don't have an account? Sign up
          </button>

          <button
            type="button"
            @click="router.push('/forgot-password')"
            class="text-sm text-primary hover:text-foreground transition-colors"
          >
            Forgot Password?
          </button>
        </div>

        <div
          id="appleid-signin"
          class="w-[210px] h-[40px]"
          data-color="black"
          data-border="true"
          data-type="sign-in"
        ></div>

        <GoogleSignInButton text="signin_with" @success="onGoogleSignIn" />
      </form>
    </div>
  </div>
</template>
<script setup>
import { onGoogleSignIn, onFailure, onAppleSignIn } from "@/utils/sso";

useScript(
  "https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js"
);

let auth = useNuxtApp().$auth;
let $api = useNuxtApp().$api;

let router = useRouter();
let route = useRoute();

let valid = ref();

let email = ref();
let password = ref();
let resetCode = ref();

let error = ref();

let passwordInput = useTemplateRef("passwordInput");
let passwordResetDialog = ref(false);
let showPasswordResetCode = ref(false);
let isLoading = ref(false);

function navigateToSignUp() {
  let redeem = route.query.redeem;
  let url = "/signup";
  if (redeem) {
    url = "/signup?redeem=" + redeem;
  }

  navigateTo(url);
}

async function submit() {
  try {
    isLoading.value = true;
    let user = await auth.login(email.value, password.value);
    if (!user) {
      error.value = "Invalid email or password";
    }
    if (route.query.redeem) {
      navigateTo(`/redeem/${route.query.redeem}`);
      return;
    }

    navigateTo(`/`);
  } catch (exc) {
    console.error(exc);
    error.value = "Authentication Error";
  } finally {
    isLoading.value = false;
    console.log("Error", error.value);
  }
}

async function beginSubmitPasswordReset() {
  try {
    await auth.beginResetPassword(email.value);
    showPasswordResetCode.value = true;
  } catch (e) {
    console.error(e);
  }
}

async function submitPasswordReset() {
  try {
    await auth.resetPassword(email.value, resetCode.value, password.value);
    showPasswordResetCode.value = false;
    passwordResetDialog.value = false;
  } catch (e) {
    console.error(e);
  }
}

function cancelPasswordReset() {
  loginDialog.value = true;
  passwordResetDialog.value = false;

  showPasswordResetCode.value = false;
  resetCode.value = "";
}

function resetPassword() {
  loginDialog.value = false;
  passwordResetDialog.value = true;
}

onMounted(() => {
  if (route.query.postReset) {
    console.log("focusing", route.query.postReset);
    email.value = route.query.postReset;
    if (passwordInput.value && passwordInput.value.focus)
      passwordInput.value.focus();
  }

  document.addEventListener("AppleIDSignInOnSuccess", onAppleSignIn);
  document.addEventListener("AppleIDSignInOnFailure", onFailure);
});

onUnmounted(() => {
  document.removeEventListener("AppleIDSignInOnSuccess", onAppleSignIn);
  document.removeEventListener("AppleIDSignInOnFailure", onFailure);
});

let runtimeConfig = useRuntimeConfig();

let nonce = await useApi("/apple-nonce");

useHead({
  meta: [
    {
      name: "appleid-signin-client-id",
      content: runtimeConfig.public.appleServicesId,
    },
    { name: "appleid-signin-scope", content: "name email" },
    {
      name: "appleid-signin-redirect-uri",
      content: runtimeConfig.public.baseAppUrl + "/signin",
    },
    { name: "appleid-signin-state", content: "origin:web" },
    { name: "appleid-signin-nonce", content: nonce.data.value.nonce },
    { name: "appleid-signin-use-popup", content: "true" },
  ],
});
onMounted(() => {
  if (window && window.AppleID) {
    window.AppleID.auth.init({
      usePopup: true,
    });
  }
});
</script>
