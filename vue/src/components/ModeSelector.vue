<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { state } from "../store";

const route = useRoute();
const scoringApp = computed(() => state.dataSource === 'scoring');
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
      :to="scoringApp ? '/scoring/' : '/'"
      :color="!proposalView? 'primary': ''"
      :theme="!proposalView? 'dark': ''"
      class="mx-2"
    >
      Analyst
    </v-btn>
    <v-btn
      :to="scoringApp ? '/scoring/proposals' : '/proposals'"
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
