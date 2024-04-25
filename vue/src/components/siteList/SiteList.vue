<script setup lang="ts">
import { Ref, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { ApiService } from "../../client";
import {
  DownloadSettings,
} from "../../client/services/ApiService";
import { clickedInfo, hoveredInfo } from "../../interactions/mouseEvents";
import ImagesDownloadDialog from "../ImagesDownloadDialog.vue";
import SiteListCard from "./SiteListCard.vue";
import { SiteDisplay } from "./SiteListCard.vue";
import SiteListHeader from "./SiteListHeader.vue";
import SiteListFilter from "./SiteListFilter.vue";
import { getSiteObservationDetails, state } from "../../store";

const props = defineProps<{
  modelRuns: string[];
}>();

const baseModifiedList: Ref<SiteDisplay[]> = ref([]);
const modifiedList: Ref<SiteDisplay[]> = ref([]);
const imageDownloadDialog = ref(false);
const imageTimeRange: Ref<{min: number, max: number} | null> = ref(null);
const imageDownloadingId: Ref<null | string> = ref(null)
const modelRunTitleList: Ref<string[]> = ref([])
const totalCount: Ref<number> = ref(0);
const filter = ref("");


const getSites = async (modelRun: string) => {
    const results = await ApiService.getSitesList(modelRun);
    state.selectedSites = [];
    totalCount.value = 0;
    const regionName = results.region;
    let newNumbers = 0;
    if (results.sites) {
      const modList: SiteDisplay[] = [];
      let selected: SiteDisplay | null = null;
      const details = results.modelRunDetails ? {
        title: results.modelRunDetails.title,
        version: results.modelRunDetails.version,
        performer: results.modelRunDetails.performer.short_code,
        region: results.modelRunDetails.region,
        proposal: results.modelRunDetails.proposal,
      } : undefined

      const selectedIds = state.selectedSites.map((item) => item.id);
      results.sites.forEach((item) => {
        const newNum = item.number.toString().padStart(4, "0");
        if (newNum === "9999") {
          newNumbers += 1;
        }
        let name = `${regionName}_${newNum}`;
        if (newNumbers > 1) {
          name = `${name}-${newNumbers}`;
        }
        modList.push({
          number: item.number,
          id: item.id,
          name,
          filename: item.filename,
          bbox: item.bbox,
          selected: selectedIds.includes(item.id),
          images: item.images,
          startDate: item.start_date,
          endDate: item.end_date,
          S2: item.S2,
          WV: item.WV,
          L8: item.L8,
          PL: item.PL,
          status: item.status,
          timestamp: item.timestamp,
          downloading: item.downloading,
          details,
          proposal: !!details?.proposal,
        });
        modelRunTitleList.value.push(details?.title || '');
        totalCount.value += 1;
      });
      // We need to start checking if there are downloading sites to update every once in a while
      if (selected !== null) {
        selectSite(selected);
      }
      return modList;
    }
    return [];
};

const getAllSiteProposals = async () => {
    let mainList: SiteDisplay[] = [];
    for (let i = 0; i < props.modelRuns.length; i += 1) {
        const results = await getSites(props.modelRuns[i]);
        mainList = mainList.concat(results);
    }
    baseModifiedList.value = mainList;
    modifiedList.value = mainList;
}
onMounted(() => getAllSiteProposals());

watch(
  () => props.modelRuns,
  () => {
    getAllSiteProposals();
  }
);
watch(clickedInfo, () => {
  if (clickedInfo.value.siteId.length) {
    const found = modifiedList.value.find(
      (item) => item.id === clickedInfo.value.siteId[0]
    );
    if (found !== undefined) {
      selectSite(found);
    }
  }
  // No else case, because if not clicked we don't do anything
});


const selectSite = async (selectedSite: SiteDisplay, deselect= false) => {
  if (selectedSite && !deselect) {
  await getSiteObservationDetails(selectedSite.id, undefined, true);

  }
  if (state.selectedImageSite) {
    state.selectedImageSite = undefined;
  }
  const updatedList: SiteDisplay[] = [];
  const selectedIds = state.selectedSites.map((item) => item.id);
  baseModifiedList.value.forEach((item) => {
    item.selected = selectedIds.includes(item.id)
    updatedList.push(item);
  })
  updatedList.sort((a, b) => {
        if (a.selected === b.selected) {
          return 0;
        }
        if (a.selected) {
          return -1;
        }
        return 1;
      });
  modifiedList.value = updatedList;
  if (!deselect) {
    nextTick(() => {
      const id = selectedSite.id;
      const el = document.getElementById(`site-id-${id}`);
      if (el) {
        el.scrollIntoView({block: 'end', behavior: 'smooth'});
      }
    });
  }
}

const controlKeyPressed = ref(false);

// Function to toggle the ref value based on the key event
const toggleControlKey = (event: KeyboardEvent) => {
  controlKeyPressed.value = event.ctrlKey;
};

// Add event listener when the component is mounted
onMounted(() => {
  window.addEventListener('keydown', toggleControlKey);
  window.addEventListener('keyup', toggleControlKey);
});

// Remove event listener when the component is unmounted
onUnmounted(() => {
  window.removeEventListener('keydown', toggleControlKey);
  window.removeEventListener('keyup', toggleControlKey);
});

watch(() => hoveredInfo.value.siteId, () => {
  if (hoveredInfo.value.siteId.length && controlKeyPressed.value) {
    const id = hoveredInfo.value.siteId[0];
    const el = document.getElementById(`site-id-${id}`);
    if (el) {
      el.scrollIntoView({block: 'end', behavior: 'smooth'});
    }
  }
});
const setImageDownloadDialog = (item: SiteDisplay) => {
  if (item.startDate && item.endDate) {
    imageTimeRange.value = {
      min: item.startDate,
      max: item.endDate,
    }
  } else {
    imageTimeRange.value = null;
  }
  imageDownloadDialog.value = true;
  imageDownloadingId.value = item.id;
};

const startDownload = async (data: DownloadSettings) => {
  const id = imageDownloadingId.value;
  imageDownloadDialog.value = false;
  if (id) {
  await ApiService.getObservationImages(id, data);
    // Now we get the results to see if the service is running
    setTimeout(() => getAllSiteProposals(), 500);
  }
}
watch(filter, () => {
  if (filter.value) {
    modifiedList.value = baseModifiedList.value.filter((item) => item.name.includes(filter.value))
  } else {
    modifiedList.value = baseModifiedList.value;
  }
});

</script>

<template>
  <v-card>
    <v-card-title>
      <v-row>
        <h5>Site Models <SiteListFilter :model-runs="modelRunTitleList" /></h5>
        <v-spacer />
        <span>
          <v-icon size="xsmall">mdi-map-marker-outline</v-icon><span>{{ totalCount }}</span>
        </span>
      </v-row>
    </v-card-title>
    <site-list-header v-model="filter" />
    <div class="proposal-list">
      <div
        v-if="state.selectedSites && state.selectedSites.length > 0"
        class="selected-header"
      >
        Selected Sites
      </div>
      <div
        v-else
        style="height:20px"
      />
      <v-virtual-scroll
        height="calc(100vh - 145px)"
        :items="modifiedList"
        item-height="200"
      >
        <template #default="{item}">
          <site-list-card
            :key="item.id"
            :site="item"
            @selected="selectSite(item)"
            @close="selectSite(item, true)"
            @image-download="setImageDownloadDialog($event)"
          />
        </template>
      </v-virtual-scroll>
    </div>
    <images-download-dialog
      v-if="imageDownloadDialog"
      :date-range="imageTimeRange"
      @download="startDownload($event)"
      @cancel="imageDownloadDialog = false"
    />
  </v-card>
</template>

<style scoped>

.title {
  font-size: 12px;
}
.errorCard {
  background-color: lightcoral;
}
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.selected-header {
  height: 20px;
  background-color: #FFF9C4;
}


.proposal-list {
  position: sticky;
  top: 0px;
  z-index: 2;
  background-color: white;
  overflow-y: auto;
  max-height: calc(100vh - 125px);
}

</style>
