

<script setup lang="ts">
import { PopUpData } from '../interactions/popUpType';
const props = defineProps<{
  data:PopUpData[]
}>();

</script>

<template>
  <v-card dense>
    <v-row
      v-for="item in props.data"
      :key="item.siteId"
      dense
      align="center"
      class="ma-5"
    >
      <v-chip
        label
        :color="item.siteColor"
        class="mx-2"
      >
        <v-icon
          v-if="item.groundTruth"
          size="small"
          :color="item.siteColor"
        >
          mdi-check-decagram
        </v-icon>
        SiteId: {{ item.siteId }}
      </v-chip>
      <v-chip
        label
        :color="item.scoreColor"
        class="mx-2"
      >
        Score: {{ item.score.toFixed(2) }}
      </v-chip>
      <v-chip
        label
        color="black"
        variant="elevated"
        class="mx-2"
      >
        Area: {{ item.area }}m²
      </v-chip>
    </v-row>
  </v-card>
</template>
