<script setup lang="ts">
import ErrorPopup from './components/ErrorPopup.vue';

import { onErrorCaptured, ref } from "vue";

const errorText = ref('');

onErrorCaptured((err) => {
  const error: Record<string, string> = {};
  for (const [key, val] of Object.entries(err)) {
    error[key] = JSON.stringify(val);
  }
  errorText.value = JSON.stringify(error);
  throw err;
});
</script>

<template>
  <div>
    <ErrorPopup
      :error-text="errorText"
      @close="errorText = ''"
    />
    <v-app id="RGD">
      <router-view />
    </v-app>
  </div>
</template>
