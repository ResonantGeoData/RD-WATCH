

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
    sortable: false,
  },

  SiteId:{
    title: 'Id',
    key: 'siteId',
    width:"10px",
    align:"center",
    sortable: false,
  },
  ModelRun:{
    title: 'Name',
    key: 'modelRun',
    width:"10px",
    align:"center",
    sortable: false,
  },
  Performer:{
    title: 'Performer',
    key: 'performerName',
    width:"10px",
    align:"center",
    sortable: false,
  },
  Status:{
    title: 'Status',
    key: 'status',
    width:"20px",
    sortable: false,
  },
  Time:{
    title: 'Time Range',
    key:'timestamp',
    width:"100px",
    sortable: false,
  },
  Score:{
    title: 'Score',
    key:'score',
    width:"10px",
    sortable: false,
  },
  Area:{
    title: 'Area',
    key:'area',
    width:"10px",
    sortable: false,
  },
  ObsLabel:{
    title: 'Observation',
    key:'obsLabel',
    width:"10px",
    sortable: false,
  }
}

const headers = computed( () => {
  // inject headers into the system
  const headers: {title: string, key: string; width: string; sortable?: boolean}[] = [];
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
  if (state.toolTipDisplay.ObsLabel && items.value.findIndex((item) => ( (item as PopUpData).area)) !== -1) {
    headers.push(headerMapping['ObsLabel']);
  }

  return headers;
  });


const items = computed(() => {
  const items: (PopUpData & PopUpSiteData)[] = [];
  Object.values(props.data).forEach((item) => {
    items.push(item);
  });
  Object.values(props.siteData).forEach((item) => {
    items.push(item);
  });
  return items;
});

const columns = computed(() => Object.keys(state.toolTipDisplay));

</script>

<template>
  <v-card
    dense
    variant="flat"
  >
    <v-row class="py-4">
      <v-spacer />
      <v-menu
        id="tooltip-menu"
        v-model="state.toolTipMenuOpen"
        open-delay="20"
        :close-on-content-click="false"
        location="start"
      >
        <template #activator="{ props }">
          <v-icon
            color="primary"
            v-bind="props"
            size="20"
            class="mr-5"
          >
            mdi-cog
          </v-icon>
        </template>
        <v-card
          class="pa-4"
          style="overflow-y: hidden;"
        >
          <v-row
            v-for="column in columns"
            :key="column"
            density="compact"
          >
            <v-checkbox
              v-model="state.toolTipDisplay[column]"
              style="max-height: 30px;"
              color="primary"
              density="compact"
              :label="column"
            />
          </v-row>
        </v-card>
      </v-menu>
    </v-row>
    <v-row dense>
      <v-card dense>
        <v-data-table
          density="compact"
          :headers="headers"
          :items="items"
          class="tooltip"
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
          <template #[`item.obsLabel`]="{ item }">
            <v-chip
              label
              :color="item.obsColor || 'gray'"
              size="x-small"
              density="compact"
              class="mx-1"
            >
              {{ item.obsLabel || 'NA' }}
            </v-chip>
          </template>
          <template #bottom />
        </v-data-table>
      </v-card>
    </v-row>
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