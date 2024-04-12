<script setup lang="ts">
import {
  ApiService,
  SiteModelStatus,
} from "../../client/services/ApiService";
import { SiteObservation, getSiteObservationDetails, state, toggleSatelliteImages } from "../../store";
import { timeRangeFormat } from "../../utils";
import { Ref, computed, ref, watch } from "vue";
import { hoveredInfo } from "../../interactions/mouseEvents";
import ImageBrowser from './ImageBrowser.vue';
export interface SiteDisplay {
  number: number;
  id: string;
  uuid?: string;
  name: string;
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  startDate: number;
  endDate: number;
  selected: boolean;
  filename?: string | null;
  images: number;
  S2: number;
  WV: number;
  L8: number;
  PL: number;
  status?: SiteModelStatus;
  timestamp: number;
  downloading: boolean;
  proposal?: boolean;
  details?: {
    performer: string;
    version: string;
    region: string;
    title: string;
  };
}

const props = defineProps<{
    site: SiteDisplay;
    selectedEval: string | null;
}>();
const emit = defineEmits<{
  (e: "selected", val: SiteDisplay | null): void;
  (e: "clicked", { uuid } : { uuid: string }): void;
  (e: "image-download", val: SiteDisplay): void;
}>();
let downloadCheckInterval: NodeJS.Timeout | null = null;

const localSite: Ref<SiteDisplay> = ref({...props.site});

const selectedSite: Ref<undefined | SiteObservation> = ref(undefined)

watch(state.selectedObservations, () => {
  selectedSite.value  = state.selectedObservations.find((item) => item.id === localSite.value.id);
  selectSite.value = !!selectedSite.value;
});

const selectSite = ref(!!selectedSite.value)

const imagesActive = computed(() => state.enabledSiteObservations.findIndex((item) => item.id === props.site.id) !== -1);
const hasImages = computed(() =>  props.site.WV > 0 || props.site.S2 > 0 || props.site.PL > 0 || props.site.L8 > 0);



const statusMap: Record<SiteModelStatus, { name: string; color: string, icon: string }> = {
  PROPOSAL: { name: "Proposed", color: "orange", icon: "mdi-dots-horizontal-circle" },
  REJECTED: { name: "Rejected", color: "error", icon: "mdi-alert-circle" },
  APPROVED: { name: "Approved", color: "success", icon: "mdi-check-circle" },
};

const reloadSiteData = async () => {
  const data = await ApiService.getSite(localSite.value.id);
  localSite.value = {...props.site, ...data};
  if (!localSite.value.downloading && downloadCheckInterval) {
    clearInterval(downloadCheckInterval);
  }
}

watch(() => props.site, () => {
  if (props.site.downloading){
        downloadCheckInterval = setInterval(() => reloadSiteData(), 5000);
  } else {
    if (downloadCheckInterval !== null) {
      clearInterval(downloadCheckInterval);
    }
  }
});


const download = (id: string) => {
  const url = `/api/evaluations/${id}/download`;
  window.location.assign(url);
};

const setImageDownloadDialog = () => {
    emit('image-download', localSite.value)
};

const cancelTask = async () => {
  await ApiService.cancelSiteObservationImageTask(localSite.value.id);  
}


const close = () => {
const foundIndex = state.selectedObservations.findIndex((item) => item.id === props.site.id);
  if (foundIndex !== -1) {
    toggleSatelliteImages(state.selectedObservations[foundIndex], true);
    state.selectedObservations.splice(foundIndex, 1);
  }
}


watch(selectSite, async () => {
  if (selectSite.value) {
    emit('selected', props.site)
    getSiteObservationDetails(props.site.id);
  } else {
    close();
  }
})

</script>

<template>
  <v-card
    :id="`site-id-${localSite.id}`"
    :key="`${localSite.name}_${localSite.id}_${localSite.selected}`"
    variant="flat"
    class="siteCard"
    :class="{
      selectedCard: site.selected,
      hoveredCard: hoveredInfo.siteId.includes(localSite.id),
    }"
    @mouseenter="state.filters.hoverSiteId = localSite.id"
    @mouseleave="state.filters.hoverSiteId = undefined"
  >
    <v-card-title class="title">
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col><span> {{ localSite.name }}</span></v-col>
        <v-spacer />
        <v-col
          v-if="localSite.status"
          cols="1"
          class="mr-4"
        >
          <v-tooltip
            open-delay="0"
            bottom
          >
            <template #activator="{ props }">
              <v-icon 
                size="20"
                class="pa-0 ma-0 site-icon"
                :color="statusMap[localSite.status].color"
                v-bind="props"
              >
                {{ statusMap[localSite.status].icon }}
              </v-icon>
            </template>
            <span> {{ statusMap[localSite.status].name }} </span>
          </v-tooltip>
        </v-col>
        <v-col
          v-if="!localSite.proposal"
          cols="1"
        >
          <v-checkbox-btn
            v-model="selectSite"
            density="compact"
            color="#29B6F6"
            hide-details
          />
        </v-col>
      </v-row>
    </v-card-title>
    <v-card-text>
      <v-row
        v-if="!localSite.proposal && localSite.details"
        dense
      >
        <span class="site-model-info"> {{ localSite.details.performer }} {{ localSite.details.title }}: {{ localSite.details.version }} </span>
      </v-row>
      <v-row
        v-if="!localSite.proposal"
        dense
      >
        <span class="site-model-info-label">Date Range:</span><span class=" ml-1 site-model-dates"> {{ timeRangeFormat({min: site.startDate, max: site.endDate }) }} </span>
      </v-row>
      <v-row
        v-if="!localSite.proposal && selectedSite"
        dense
        justify="center"
        align="center"
      >
        <div class="site-model-info-label">
          Score:
        </div>
        <div class="site-model-data-label">
          {{ selectedSite.score.min.toFixed(2) }} to {{ selectedSite.score.max.toFixed(2) }}
        </div>
        <v-spacer />
      </v-row>
      <v-row
        v-if="!localSite.proposal && selectedSite"

        dense
        justify="center"
        align="center"
      >
        <div class="site-model-info-label">
          Average:
        </div>
        <div class="site-model-data-label">
          {{ selectedSite.score.average.toFixed(2) }}
        </div>
        <v-spacer />
      </v-row>
      <v-row
        v-if="localSite.images"
        dense
      >
        <v-col>
          <span class="image-label">WV:</span>
          <span class="image-value">{{ localSite.WV }}</span>
        </v-col>
        <v-col cols="1">
          <span class="image-line" />
        </v-col>
        <v-col>
          <span class="image-label">S2:</span>
          <span class="image-value">{{ localSite.S2 }}</span>
        </v-col>
        <v-col cols="1">
          <span class="image-line" />
        </v-col>
        <v-col>
          <span class="image-label">L8:</span>
          <span class="image-value">{{ localSite.L8 }}</span>
        </v-col>
        <v-col cols="1">
          <span class="image-line" />
        </v-col>
        <v-col>
          <span class="image-label">PL:</span>
          <span class="image-value">{{ localSite.PL || 0 }}</span>
        </v-col>
      </v-row>
      <v-row
        v-else
        align="center"
      >
        <span class="no-images">No Images Downloaded</span>
      </v-row>
      <v-row
        dense
        class="pt-2"
      >
        <v-tooltip
          v-if="localSite.filename"
          open-delay="0"
          bottom
        >
          <template #activator="{ props }">
            <v-icon
              size="small"
              class="pa-0 ma-1 site-icon"
              v-bind="props"
            >
              mdi-file-question-outline
            </v-icon>
          </template>
          <span>
            {{ localSite.filename }}
          </span>
        </v-tooltip>
        <v-tooltip
          v-else-if="!localSite.filename && selectedSite"
          open-delay="300"
        >
          <template #activator="{ props }">
            <v-btn
              variant="tonal"
              density="compact"
              class="pa-0 ma-1 site-icon"
              size="small"
              :color="imagesActive ? 'success': ''"
              v-bind="props"
              @click.stop="hasImages && toggleSatelliteImages(selectedSite)"
            >
              <v-icon size="small">
                mdi-image
              </v-icon>
            </v-btn>
          </template>
          <span>Toggle Site Images</span>
        </v-tooltip>
        <v-spacer />
        <v-tooltip open-delay="300">
          <template #activator="{ props }">
            <v-btn
              variant="tonal"
              density="compact"
              class="pa-0 ma-1 site-icon"
              size="small"
              color="primary"
              v-bind="props"
              @click.stop="download(localSite.id)"
            >
              <v-icon size="small">
                mdi-export
              </v-icon>
            </v-btn>
          </template>
          <span>Download JSON</span>
        </v-tooltip>
        <v-tooltip
          v-if="!localSite.downloading"
          open-delay="300"
        >
          <template #activator="{ props }">
            <v-btn
              variant="tonal"
              density="compact"
              class="pa-0 ma-1 site-icon"
              size="small"
              color="primary"
              v-bind="props"
              @click.stop="setImageDownloadDialog()"
            >
              <v-icon>mdi-image-sync</v-icon>
            </v-btn>
          </template>
          <span>Download Satellite Images</span>
        </v-tooltip>
        <div v-else-if="localSite.downloading">
          <v-tooltip open-delay="300">
            <template #activator="{ props }">
              <v-btn
                variant="tonal"
                density="compact"
                class="pa-0 ma-1 site-icon animate-flicker"
                size="xmall"
                color="warning"
                v-bind="props"
              >
                <v-icon>mdi-image-sync</v-icon>
              </v-btn>
            </template>
            <span>Currently Downloading Images</span>
          </v-tooltip>
          <v-tooltip open-delay="300">
            <template #activator="{ props }">
              <v-btn
                variant="tonal"
                density="compact"
                class="pa-0 ma-1 site-icon"
                color="error"
                size="xmall"
                v-bind="props"
                @click.stop="cancelTask()"
              >
                <v-icon>mdi-image-remove</v-icon>
              </v-btn>
            </template>
            <span>Cancel Image Downloading</span>
          </v-tooltip>
        </div>
      </v-row>
      <ImageBrowser
        v-if="!localSite.proposal && selectedSite !== undefined"
        :site-observation="selectedSite"
      />
    </v-card-text>
    <div
      v-if="site.selected"
      class="selectedBorder"
    />
  </v-card>
</template>

<style scoped>

@keyframes flicker-animation {
  0% { opacity: 1; }
  50% { opacity: 0; }
  100% { opacity: 1; }
}

.animate-flicker {
  animation: flicker-animation 1s infinite;
}

.selectedBorder {
  background-color: #FFF9C4;
  height: 5px;
}
.siteCard {
  border: 3px solid transparent;
  border-bottom: 1px solid gray;
}
.siteCard:hover {
  cursor: pointer;
  border: 3px solid #188DC8;
}

.title {
  font-size: 12px;
}

.errorCard {
  background-color: lightcoral;
}

.hoveredCard {
  background-color: orange;
  border: 3px solid orange;
}

.selectedCard {
  background-color: #e8f1f8;
}

.image-label {
  font-size: 12px;
  color: gray;
}
.image-value {
  font-size: 12px;
  color: black;
  font-weight: bolder;
}
.image-line {
  margin-left: 5px;
  border-right: 1px solid gray;
}
.site-icon {
  min-width: 25px;
  min-height: 25px;;
}
.no-images {
  font-size:14px;
  color: red;
}
.site-model-info {
  font-size: 12px;
}
.site-model-info-label {
  color: gray;
  font-size: 12px;
}
.site-model-data-label {
  color: black;
  font-size: 12px;

}

.site-dates-label {
  color: gray
}
.site-model-dates {
  font-size: 10px;
}
</style>
