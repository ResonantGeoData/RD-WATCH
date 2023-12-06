<script setup lang="ts">
import { state } from './store';

import { onErrorCaptured } from "vue";

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
  <v-app id="RGD">
    <router-view />
  </v-app>
</template>
