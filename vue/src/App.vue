<script setup lang="ts">
import { state } from './store';

import { onBeforeMount, onErrorCaptured, ref } from "vue";

const isLoggedIn = ref(false);

// Check if the user is logged in before rendering any UI. If they're not,
// redirect them to the login page.
onBeforeMount(async () => {
  try {
    await fetch('/api/status/', { redirect: 'error' });
    isLoggedIn.value = true;
  } catch (e) {
    window.location.href = `/accounts/gitlab/login/?next=${window.location.pathname}`;
  }
});

onErrorCaptured((err) => {
  const error: Record<string, string> = {};
  for (const [key, val] of Object.entries(err)) {
    error[key] = JSON.stringify(val);
  }
  // Also include a string-ified version of the exception object.
  error['error_string'] = err.toString();
  state.errorText = JSON.stringify(error);
  throw err;
});
</script>

<template>
  <v-app
    v-if="isLoggedIn"
    id="RGD"
  >
    <router-view />
  </v-app>
</template>
