<script setup lang="ts">
import ErrorPopup from './components/ErrorPopup.vue';

import { onErrorCaptured, ref } from "vue";

const errorText = ref('');

onErrorCaptured((err) => {
  errorText.value = [err.name, err.message, err.stack, err.cause].join('\n\n');
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
