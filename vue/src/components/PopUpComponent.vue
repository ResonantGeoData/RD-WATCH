

<script setup lang="ts">
import { computed } from 'vue';
import { PopUpData, PopUpSiteData } from '../interactions/popUpType';
import { state } from '../store';
const props = defineProps<{
  data:Record<string, PopUpData>;
  siteData:Record<string, PopUpSiteData>;
}>();

const headerMapping = {
  Type:{
    title: 'Type',
    key: 'type',
    width:"10px",
  },

  SiteId:{
    title: 'Id',
    key: 'siteId',
    width:"10px",
    align:"center",
  },
  ModelRun:{
    title: 'Name',
    key: 'modelRun',
    width:"10px",
    align:"center",
  },
  Performer:{
    title: 'Performer',
    key: 'performerName',
    width:"10px",
    align:"center",
  },
  Status:{
    title: 'Status',
    key: 'status',
    width:"20px",
  },
  Time:{
    title: 'Time Range',
    key:'timestamp',
    width:"100px",
  },
  Score:{
    title: 'Score',
    key:'score',
    width:"10px",
  },
  Area:{
    title: 'Area',
    key:'area',
    width:"10px",
  }
}

const headers = computed( () => {
  // inject headers into the system
  const headers: {title: string, key: string; width: string}[] = [];
  if (state.toolTipDisplay.Type) {
    headers.push(headerMapping['Type']);
  }
  if (state.toolTipDisplay.SiteId) {
    headers.push(headerMapping['SiteId']);
  }
  if (state.toolTipDisplay.Performer) {
    headers.push(headerMapping['Performer']);
  }
  if (state.toolTipDisplay.ModelRun) {
  headers.push(headerMapping['ModelRun']);
  }
  if (state.toolTipDisplay.Status) {
  headers.push(headerMapping['Status']);
  }
  if (state.toolTipDisplay.Time) {
  headers.push(headerMapping['Time']);
  }
  if (state.toolTipDisplay.Score && items.value.findIndex((item) => ( item.scoreColor || (item as PopUpData).score !== undefined )) !== -1) {
    headers.push(headerMapping['Score']);
  }
  if (state.toolTipDisplay.Area && items.value.findIndex((item) => ( (item as PopUpData).area)) !== -1) {
    headers.push(headerMapping['Area']);
  }

  return headers;
  });


const items = computed(() => {
  const items: (PopUpData | PopUpSiteData)[] = [];
  Object.values(props.data).forEach((item) => {
    items.push(item);
  });
  Object.values(props.siteData).forEach((item) => {
    items.push(item);
  });
  return items;
})


</script>

<template>
  <v-card dense>
    <v-data-table
      density="compact"
      :headers="headers"
      :items="items"
      class="tooltip ma-0 pa-0"
    >
      <template #[`item.type`]="{ item }">
        {{ item.timestamp === undefined ? 'Site' : 'Obs' }}
      </template>

      <template #[`item.modelRun`]="{ item }">
        <div class="smallDisplay">
          {{ item.configName }}: V{{ item.version }}
        </div>
      </template>
      <template #[`item.siteId`]="{ item }">
        <v-chip
          label
          :color="item.obsColor"
          size="x-small"
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
          {{ item.siteId }}
        </v-chip>
      </template>

      <template #[`item.status`]="{ item }">
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
      </template>
      <template #[`item.timestamp`]="{ item}">
        <div class="smallDisplay">
          <div v-if="item.timestamp">
            {{ item.timestamp.substring(0,10) }}
          </div>
        
          <div v-else-if="item.timestamp !== undefined">
            <v-icon size="x-small">
              mdi-clock
            </v-icon>: NULL
          </div>
          <div v-if="item.timeRange">
            {{ item.timeRange }}
          </div>
        </div>
      </template>
      <template #[`item.score`]="{item}">
        <div
          v-if="item.score"
        >
          {{ item.score.toFixed(2) }}
        </div>

        <v-chip
          v-if="item.scoreLabel && item.scoreColor"
          label
          variant="elevated"
          :color="item.scoreColor"
          size="small"
          density="compact"
          class="mx-1"
        >
          {{ item.scoreLabel }}
        </v-chip>
      </template>
      <template #[`item.area`]="{item}">
        <div
          v-if="item.area"
        >
          {{ item.area }}m²
        </div>
      </template>

      <template #bottom />
    </v-data-table>
  </v-card>
</template>

<style scoped>
.tooltip {
  font-size: 0.75em;
}
.smallDisplay {
  font-size: 0.75em;
}
</style>