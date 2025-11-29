<template>
  <ClientOnly> Hello: {{ $auth?.user?.name }} </ClientOnly>
</template>

<script setup>
const { $auth } = useNuxtApp();

if ($auth) {
  let user = await $auth.getUser();
  console.log("User in setup:", user);
}
</script>
