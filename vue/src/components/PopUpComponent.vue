

<script setup lang="ts">
import { PopUpData } from '../interactions/popUpType';
const props = defineProps<{
  data:PopUpData[]
}>();

</script>

<template>
  <v-card dense style="z-index:1000">
    <v-row
      v-for="item in props.data"
      :key="item.siteId"
      dense
      align="center"
      justify="center"
      class="my-2"
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
      <v-chip
        v-if="item.timestamp"
        label
        variant="elevated"
        class="mx-2"
      >
        <v-icon size="x-small">
          mdi-clock
        </v-icon>: {{ item.timestamp.substring(0,10) }}
      </v-chip>
    </v-row>
  </v-card>
</template>
