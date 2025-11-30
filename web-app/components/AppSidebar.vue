<template>
  <Sidebar
    v-if="$route.path !== '/signin' && $route.path !== '/signup'"
    class="font-standard"
  >
    <SidebarHeader class="font-standard">
      <NuxtLink to="/" class="flex items-center gap-2 px-4 py-3">
        <SidebarMenuButton class="text-lg">
          <House class="w-5 h-5" />
          Dashboard
        </SidebarMenuButton>
      </NuxtLink>
    </SidebarHeader>
    <SidebarContent> </SidebarContent>
    <SidebarFooter class="font-standard">
      <DropdownMenu v-if="user">
        <DropdownMenuTrigger as-child>
          <SidebarMenuButton class="pl-2 pr-4">
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
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent class="w-56 font-standard">
          <DropdownMenuLabel class="max-sm:hidden"
            >My Account
          </DropdownMenuLabel>
          <DropdownMenuLabel class="md:hidden">
            {{ user ? user.name : "My Account" }}
          </DropdownMenuLabel>
          <DropdownMenuItem
            @click="$auth.logout()"
            v-if="user"
            class="text-muted-foreground hover:text-primary"
          >
            <LogOut class="h-4 w-4" />
            Sign Out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <NuxtLink v-else to="/signin" class="w-full">
        <Button class="w-full"> Sign In </Button>
      </NuxtLink>
    </SidebarFooter>
  </Sidebar>
</template>

<script setup>
import { House, User, LogOut } from "lucide-vue-next";

const { $auth } = useNuxtApp();

const user = computed(() => $auth?.user || null);
</script>
