

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
      justify="center"
      class="my-1"
    >
      <v-row
        dense
        align="center"
        justify="center"
      >
        <v-chip
          label
          size="small"
          density="compact"
          class="mx-1 mb-1"
        >
          {{ item.performerName }} : {{ item.configName }}: V{{ item.version }}
        </v-chip>
      </v-row>
      <v-row
        dense
        align="center"
        justify="center"
        class="mb-1"
      >
        <v-chip
          label
          :color="item.siteColor"
          size="small"
          density="compact"
          class="mx-1"
        >
          <v-icon
            v-if="item.groundTruth"
            size="small"
            :color="item.siteColor"
          >
            mdi-check-decagram
          </v-icon>
          {{ item.siteLabel }}
        </v-chip>

        <v-chip
          label
          :color="item.obsColor"
          size="small"
          density="compact"
          class="mx-1"
        >
          <v-icon
            v-if="item.groundTruth"
            size="small"
            :color="item.obsColor"
          >
            mdi-check-decagram
          </v-icon>
          SiteId: {{ item.siteId }}
        </v-chip>
        <v-chip
          label
          :color="item.scoreColor"
          size="small"
          density="compact"
          class="mx-1"
        >
          Score: {{ item.score?.toFixed(2) }}
        </v-chip>
        <v-chip
          label
          color="black"
          variant="elevated"
          size="small"
          density="compact"
          class="mx-1"
        >
          Area: {{ item.area }}m²
        </v-chip>
        <v-chip
          v-if="item.timestamp"
          label
          variant="elevated"
          size="small"
          density="compact"
          class="mx-1"
        >
          <v-icon size="x-small">
            mdi-clock
          </v-icon>: {{ item.timestamp.substring(0,10) }}
        </v-chip>
        <v-chip
          v-else-if="item.timestamp === undefined"
          label
          variant="elevated"
          size="small"
          density="compact"
          class="mx-1"
        >
          <v-icon size="x-small">
            mdi-clock
          </v-icon>: NULL
        </v-chip>
      </v-row>
    </v-row>
  </v-card>
</template>
