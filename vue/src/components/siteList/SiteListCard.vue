<script setup lang="ts">
import {
  ApiService,
  SiteModelStatus,
} from "../../client/services/ApiService";
import { SiteOverview, state, toggleSatelliteImages } from "../../store";
import { timeRangeFormat } from "../../utils";
import { Ref, computed, ref } from "vue";
import { hoveredInfo } from "../../interactions/mouseEvents";
import ImageBrowser from './ImageBrowser.vue';
import ImageToggle from './ImageToggle.vue';
import AnimationDownloadDialog from "../AnimationDownloadDialog.vue";

export interface SiteDisplay {
  number: number;
  id: string;
  uuid?: string;
  modelRunId?: string;
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
  groundTruth?: boolean;
  color_code?: number;
  originator?: string;
  proposal?: boolean;
  details?: {
    performer: string;
    version: string;
    region: string;
    title: string;
  };
  selectedSite?: SiteOverview; 
}

const props = defineProps<{
    site: SiteDisplay;
}>();
const emit = defineEmits<{
  (e: "selected", val: SiteDisplay | null): void;
  (e: "clicked", { uuid } : { uuid: string }): void;
  (e: "image-download", val: SiteDisplay): void;
  (e: "close"): void;
  (e: 'cancel-download'): void;
}>();

const localSite: Ref<SiteDisplay> = ref({...props.site});




const imagesActive = computed(() => state.enabledSiteImages.findIndex((item) => item.id === props.site.id) !== -1);
const hasImages = computed(() =>  props.site.WV > 0 || props.site.S2 > 0 || props.site.PL > 0 || props.site.L8 > 0);
const downloading = computed(() => props.site.downloading);

const statusMap: Record<SiteModelStatus, { name: string; color: string, icon: string }> = {
  PROPOSAL: { name: "Proposed", color: "orange", icon: "mdi-dots-horizontal-circle" },
  REJECTED: { name: "Rejected", color: "error", icon: "mdi-alert-circle" },
  APPROVED: { name: "Approved", color: "success", icon: "mdi-check-circle" },
};


const download = (id: string) => {
  const url = `/api/evaluations/${id}/download`;
  window.location.assign(url);
};

const setImageDownloadDialog = () => {
    emit('image-download', localSite.value)
};

const cancelTask = async () => {
  await ApiService.cancelSiteObservationImageTask(localSite.value.id);
  emit('cancel-download');
}


const close = () => {
const foundIndex = state.selectedSites.findIndex((item) => item.id === props.site.id);
  if (foundIndex !== -1) {
    toggleSatelliteImages(state.selectedSites[foundIndex], true);
    state.selectedSites.splice(foundIndex, 1);
  }
  emit('close');
}


const selectingSite = async (e: boolean) => {
  if (e) {
    emit('selected', props.site)
  } else {
    close();
  }
};

const isSitePoint = (site: SiteDisplay) => {
  return Object.values(site.bbox).every(value => value === null)
}

const animationDialog = ref(false);

</script>

<template>
  <v-card
    variant="flat"
    :ripple="false"
    class="siteCard"
    :class="{
      selectedCard: site.selected,
      hoveredCard: hoveredInfo.siteId.includes(localSite.id),
    }"
    @mouseenter="state.filters.hoverSiteId = localSite.id"
    @mouseleave="state.filters.hoverSiteId = undefined"
    @click="selectingSite(!site.selected)"
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
            :model-value="site.selected"
            density="compact"
            color="#29B6F6"
            hide-details
            @update:model-value="selectingSite($event)"
          />
        </v-col>
      </v-row>
    </v-card-title>
    <v-card-text>
      <v-row
        v-if="!localSite.proposal && localSite.details"
        dense
      >
        <span
          v-if="localSite.groundTruth"
          class="pr-2"
        ><v-icon color="primary">mdi-check-decagram</v-icon></span>
        <span class="site-model-info"> {{ localSite.details.performer }} {{ localSite.details.title }}: {{ localSite.details.version }} </span>
      </v-row>

      <v-row
        v-if="!localSite.proposal"
        dense
      >
        <span class="site-model-info-label">Date Range:</span><span class=" ml-1 site-model-dates"> {{ timeRangeFormat({min: site.startDate, max: site.endDate }) }} </span>
      </v-row>
      <v-row
        v-if="!localSite.proposal && site.selectedSite"
        dense
        justify="center"
        align="center"
      >
        <div class="site-model-info-label">
          Score:
        </div>
        <div class="site-model-data-label">
          {{ site.selectedSite.score.min.toFixed(2) }} to {{ site.selectedSite.score.max.toFixed(2) }}
        </div>
        <v-spacer />
      </v-row>
      <v-row
        v-if="!localSite.proposal && site.selectedSite"

        dense
        justify="center"
        align="center"
      >
        <div class="site-model-info-label">
          Average:
        </div>
        <div class="site-model-data-label">
          {{ site.selectedSite.score.average.toFixed(2) }}
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
        <image-toggle
          v-if="!localSite.filename && site.selectedSite"
          :site-id="localSite.id"
          :site-name="localSite.name"
          :has-images="hasImages"
          :images-active="imagesActive"
          @site-toggled="hasImages && toggleSatelliteImages(site.selectedSite)"
        />
        <v-tooltip
          v-if="!localSite.filename && site.selectedSite && hasImages"
          open-delay="0"
          bottom
        >
          <template #activator="{ props }">
            <v-btn
              variant="tonal"
              density="compact"
              class="pa-0 ma-1 site-icon"
              size="small"
              v-bind="props"
              @click.stop="animationDialog = true"
            >
              <v-icon size="small">
                mdi-movie-roll
              </v-icon>
            </v-btn>
          </template>
          <span>
            Download Image Animation
          </span>
        </v-tooltip>
        <v-spacer />
        <v-tooltip 
          v-if="!ApiService.getApiPrefix().includes('scoring')"
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
          v-if="!downloading && !isSitePoint(site)"
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
              <div
                v-if="!localSite.images"
              >
                <v-icon>mdi-image-sync</v-icon>
                <v-icon
                  color="red"
                  size="20"
                  class="icon-badge"
                >
                  mdi-information
                </v-icon>
              </div>
              <v-icon v-else>
                mdi-image-sync
              </v-icon>
            </v-btn>
          </template>
          <span>
            <div v-if="!localSite.images"> No Site Images Downloaded</div>
            Click to Download Satellite Images</span>
        </v-tooltip>
        <div v-else-if="downloading">
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
        v-if="!localSite.proposal && site.selectedSite !== undefined"
        :site-overview="site.selectedSite"
      />
    </v-card-text>
    <v-dialog v-model="animationDialog" width="600">
      <animation-download-dialog
        :id="site.id"
        type="site"
        @close="animationDialog = false"
      />
    </v-dialog>
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

.siteCard {
  border: 5px solid transparent;
  padding-bottom: 4px;
  border-bottom: 1px solid gray;
}
.siteCard:hover {
  cursor: pointer;
  border: 5px solid #188DC8;
  padding-bottom: 0px;
}

.title {
  font-size: 12px;
}

.errorCard {
  background-color: lightcoral;
}

.selectedCard {
  background-color: #e8f1f8;
  border: 5px solid #FFF9C4;
  padding-bottom: 0px;

}

.hoveredCard {
  background-color: orange;
  border: 5px solid orange;
}

.image-label {
  font-size: 11px;
  color: gray;
}
.image-value {
  font-size: 11px;
  color: black;
  font-weight: bolder;
}
.image-line {
  margin-left: 1px;
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

.icon-badge {
  position: absolute;
  top: -8px;
  left: 12px;
}
</style>
