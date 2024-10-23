<script setup lang="ts">
import { state } from './store';
import type { ServerStatus } from './client';

import { onBeforeMount, onErrorCaptured, ref } from "vue";
import { initializeDataSourceConfig } from './actions/dataSource';

const isLoggedIn = ref(false);

// Check if the user is logged in before rendering any UI. If they're not,
// redirect them to the login page.
onBeforeMount(async () => {

  try {
    const data = await fetch('/api/status/', { redirect: 'error' });
    const json = await data.json();
    if (import.meta.env.DEV && json && json['detail'] === 'Unauthorized') {
      window.location.href = '/admin';
      return;
    }
    if (import.meta.env.PROD && json && json['detail'] === 'Unauthorized') {
      window.location.href = `/accounts/gitlab/login/?next=${window.location.pathname}`;
      return;
    }
    isLoggedIn.value = true;
    state.appVersion = (json as ServerStatus).rdwatch_version;
  } catch (e) {
    if (import.meta.env.PROD) {
      window.location.href = `/accounts/gitlab/login/?next=${window.location.pathname}`;
    } else {
      window.location.href = '/admin'
    }
  }

  initializeDataSourceConfig();
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
