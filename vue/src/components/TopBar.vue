<script setup lang="ts">
import LayerToggles from './topbar/LayerToggles.vue';

</script>

<template>
  <v-row
    dense
  >
    <v-row
      class="toolbar-background"
      dense
    >
      <layer-toggles />
      <v-spacer />
    </v-row>
    <v-spacer />
  </v-row>
</template>

<style scoped>
.toolbar-background {
    border-radius: 6px;
    background-color: #FFFFFFBB;
    padding-top: 10px;
    padding-bottom: 3px;
}
</style>
