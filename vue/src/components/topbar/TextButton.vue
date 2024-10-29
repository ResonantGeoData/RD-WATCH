<script setup lang="ts">
import { state } from "../../store";



const toggleText = () => {
  const val = !state.filters.showText;
  state.filters = { ...state.filters, showText: val };
}

</script>

<template>
  <v-tooltip
    location="bottom"
  >
    <template #activator="{ props: props }">
      <v-btn
        v-bind="props"
        class="px-2 mx-2"
        :variant="state.filters.showText ? undefined : 'text'"
        :color="state.filters.showText ? 'primary' : ''"
        @click="toggleText"
      >
        <v-icon
          :color="state.filters.showText ? 'white': ''"
          size="x-large"
        >
          mdi-format-text
        </v-icon>
      </v-btn>
    </template>
    <span>Toggle On/Off Text Labels</span>
  </v-tooltip>
</template>
