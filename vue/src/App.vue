<script setup lang="ts">
import ErrorPopup from './components/ErrorPopup.vue';
import { state } from './store';

import { onErrorCaptured } from "vue";

onErrorCaptured((err) => {
  const error: Record<string, string> = {};
  for (const [key, val] of Object.entries(err)) {
    error[key] = JSON.stringify(val);
  }
  state.errorText = JSON.stringify(error);
  throw err;
});
</script>

<template>
  <div>
    <ErrorPopup />
    <v-app id="RGD">
      <router-view />
    </v-app>
  </div>
</template>
