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
      <ClientOnly>
        <Button v-if="!user" @click="navigateTo('/signin')">Sign In</Button>
        <DropdownMenu v-else>
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" class="pl-2 pr-4">
              <div class="flex items-center space-x-2">
                <div
                  class="w-8 h-8 rounded-full flex items-center justify-center"
                >
                  <User class="h-4 w-4" />
                </div>
                <span class="text-sm text-muted-foreground hidden sm:block">
                  {{ user ? user.name : "Account" }}
                </span>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent class="w-56 font-standard">
            <DropdownMenuLabel class="max-sm:hidden"
              >My Account
            </DropdownMenuLabel>
            <DropdownMenuLabel class="md:hidden">
              {{ user ? user.name : "My Account" }}
            </DropdownMenuLabel>
            <DropdownMenuItem
              @click="auth.logout()"
              v-if="user"
              class="text-muted-foreground hover:text-primary"
            >
              <LogOut class="h-4 w-4" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </ClientOnly>
    </div>
  </header>
</template>

<script setup>
import { Mail, LogOut, User } from "lucide-vue-next";

const mobileMenuOpen = ref(false);
const user = ref(null);

let { $auth } = useNuxtApp();
if ($auth) {
  user.value = await $auth.getUser();
}
</script>
