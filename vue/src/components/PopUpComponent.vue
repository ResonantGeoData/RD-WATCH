<script setup lang="ts">
interface PopUpData {
  siteId: string;
  siteColor: string;
  score: number;
  groundTruth: boolean;
  scoreColor: string;
}

const data: PopUpData[] = [];
</script>

<template>
  <v-card dense>
    <v-row
      v-for="item in data"
      :key="item.siteId"
      dense
      align="center"
      class="ma-5"
    >
      <v-icon
        v-if="item.groundTruth"
        size="small"
        :color="item.siteColor"
      >
        mdi-check-decagram
      </v-icon>
      <v-chip
        label
        :color="item.siteColor"
      >
        SiteId: {{ item.siteId }}
      </v-chip>
      <v-chip
        label
        :color="item.scoreColor"
      >
        Score: {{ item.score.toFixed(2) }}
      </v-chip>
    </v-row>
  </v-card>
</template>
