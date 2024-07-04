<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const scoringApp = computed(()=> route.path.includes('scoring'));
const proposalView = computed(() => route.path.includes('proposals'));

</script>

<template>
  <v-row
    dense
    align="center"
    justify="center"
  >
    <span>Mode:</span>
    <v-btn
      to="/"
      :color="!proposalView? 'primary': ''"
      :theme="!proposalView? 'dark': ''"
      class="mx-2"
    >
      Analyst
    </v-btn>
    <v-btn
      to="/proposals"
      :color="proposalView ? 'primary': ''"
      :theme="proposalView ? 'dark': ''"
      class="mx-2"
    >
      Annotator
    </v-btn>
  </v-row>
  <v-row
    v-if="scoringApp"
    dense
  >
    <v-spacer />
    <span>Data Source:</span>
    <span><b>Scoring</b></span>
    <v-spacer />
  </v-row>
</template>
