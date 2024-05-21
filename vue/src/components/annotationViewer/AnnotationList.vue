<script setup lang="ts">
import { Ref, VueElement, onMounted, onUnmounted, ref, watch } from "vue";
import { ApiService } from "../../client";
import {
  DownloadSettings,
  SiteList,
} from "../../client/services/ApiService";
import { state, updateCameraBoundsBasedOnModelRunList } from "../../store";
import { clickedInfo, hoveredInfo } from "../../interactions/mouseEvents";
import ImagesDownloadDialog from "../ImagesDownloadDialog.vue";
import SiteListCard from "../siteList/SiteListCard.vue";
import { SiteDisplay } from "../siteList/SiteListCard.vue";
import SiteListHeader from "../siteList/SiteListHeader.vue";

const props = defineProps<{
  modelRun: string | null;
  selectedEval: string | null;
}>();

const annotationList: Ref<SiteList | null> = ref(null);
const baseModifiedList: Ref<SiteDisplay[]> = ref([]);
const modifiedList: Ref<SiteDisplay[]> = ref([]);
const imageDownloadDialog = ref(false);
const imageTimeRange: Ref<{min: number, max: number} | null> = ref(null);
const imageDownloadingId: Ref<null | string> = ref(null)
const filter = ref("");
let downloadCheckInterval: NodeJS.Timeout | null = null;
const virtualList: Ref<null | VueElement & { $el: HTMLElement } > = ref(null);

const satelliteFetchingCheck = async () => {
  const downloadList = (await ApiService.getSatelliteFetchingRunning(props.modelRun ? [props.modelRun] : [])).items;
  // Check if we are still downloading any items
  const stillDownloading = modifiedList.value.some((item) => downloadList.includes(item.id));
  if (!stillDownloading && downloadCheckInterval) {
    clearInterval(downloadCheckInterval);
    downloadCheckInterval = null;
    return;
  }
  // We want to make sure we update the list to indicate which items are downloading in the modifiedList
  const newList: SiteDisplay[] = [];
  modifiedList.value.forEach((item) => {
    if (item.downloading && !downloadList.includes(item.id)) {
      item.downloading = false;
    } else if (!item.downloading && downloadList.includes(item.id)) {
      item.downloading = true;
    }
    newList.push(item)
  });
  modifiedList.value = newList;
}


const checkDownloading = () => {
  downloadCheckInterval = setInterval(() => satelliteFetchingCheck(), 5000);
};


const getSiteProposals = async () => {
  if (props.modelRun !== null) {
    const results = await ApiService.getProposals(props.modelRun);
    annotationList.value = results;
    let newNumbers = 0;
    let downloadingAny = false;
    if (annotationList.value?.sites) {
      const modList: SiteDisplay[] = [];
      const regionName: string = annotationList.value.region;
      const accepted: string[] = [];
      const rejected: string[] = [];
      let selected: SiteDisplay | null = null;
      const details = annotationList.value.modelRunDetails ? {
        title: annotationList.value.modelRunDetails.title,
        version: annotationList.value.modelRunDetails.version,
        performer: annotationList.value.modelRunDetails.performer.short_code,
        region: annotationList.value.modelRunDetails.region,
        proposal: annotationList.value.modelRunDetails.proposal,
      } : undefined
      annotationList.value.sites.forEach((item) => {
        if (item.downloading) {
          downloadingAny = true;
        }
        const newNum = item.number.toString().padStart(4, "0");
        if (newNum === "9999") {
          newNumbers += 1;
        }
        let name = `${regionName}_${newNum}`;
        if (newNumbers > 1) {
          name = `${name}-${newNumbers}`;
        }
        if (item.status === "APPROVED") {
          accepted.push(item.id);
        } else if (item.status === "REJECTED") {
          rejected.push(item.id);
        }
        modList.push({
          number: item.number,
          id: item.id,
          name,
          filename: item.filename,
          bbox: item.bbox,
          selected: item.id === props.selectedEval,
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
        if (item.id === props.selectedEval) {
          selected = modList[modList.length - 1];
        }
      });
      state.filters.proposals = {
        accepted,
        rejected,
      };
      if (downloadingAny && downloadCheckInterval === null) {
        checkDownloading();
      }
      modifiedList.value = modList;
      baseModifiedList.value = modList;
      // We need to start checking if there are downloading sites to update every once in a while
      if (selected) {
        selectSite(selected);
      }
      
    }
  }
};
defineExpose({ getSiteProposals });

watch(
  () => props.modelRun,
  () => {
    getSiteProposals();
  }
);
watch(clickedInfo, () => {
  if (clickedInfo.value.siteId.length) {
    const found = modifiedList.value.find(
      (item) => item.id === clickedInfo.value.siteId[0]
    );
    if (found) {
      // We set the siteSelected
      if (found.L8 || found.PL || found.S2 || found.WV) {
        state.selectedImageSite = {
          siteId: found.id,
          siteName: found.name,
          dateRange: [found.startDate, found.endDate]
        }
      }
      state.bbox = found.bbox;
      scrollVirtualList(found.id);
    }
  } else {
    state.selectedImageSite = undefined;
    updateCameraBoundsBasedOnModelRunList(true, true);
  }
});

const selectSite = (item: SiteDisplay) => {
  if (item.L8 || item.PL || item.S2 || item.WV) {
    state.selectedImageSite = {
          siteId: item.id,
          siteName: item.name,
          dateRange: [item.startDate, item.endDate]
        }
  }
      state.bbox = item.bbox;
}

watch(() => props.selectedEval, () => {
  const updatedList: SiteDisplay[] = [];

  modifiedList.value.forEach((item) => {
    item.selected = props.selectedEval === item.id;
    updatedList.push(item);
  })
  modifiedList.value = updatedList;
})

watch(() => hoveredInfo.value.siteId, () => {
  if (hoveredInfo.value.siteId.length && controlKeyPressed.value) {
    const id = hoveredInfo.value.siteId[0];
    console.log('scroll to id');
    scrollVirtualList(id)
  }
});

const controlKeyPressed = ref(false);

// Function to toggle the ref value based on the key event
const toggleControlKey = (event: KeyboardEvent) => {
  controlKeyPressed.value = event.ctrlKey;
};

// Add event listener when the component is mounted
onMounted(() => {
  window.addEventListener('keydown', toggleControlKey);
  window.addEventListener('keyup', toggleControlKey);
  getSiteProposals();
});

// Remove event listener when the component is unmounted
onUnmounted(() => {
  window.removeEventListener('keydown', toggleControlKey);
  window.removeEventListener('keyup', toggleControlKey);
});
const scrollVirtualList = (id: string, itemHeight = 105) => {
  if (virtualList.value) {
    const index = modifiedList.value.findIndex((item) => item.id === id)
    console.log(`Found: index: ${index}`);
    if (index !== -1) {
      const height = (itemHeight * index) - (itemHeight * 1.25)
      console.log(height);
      virtualList.value.$el.scrollTo({top: height, left: 0, behavior: 'smooth' });
    }
  }
}

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
    setTimeout(() => getSiteProposals(), 1000);
  }
}

const cancelDownload = () => {
  setTimeout(() => getSiteProposals(), 1000);
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
  <v-card class="pb-5">
    <v-card-title><h5>Site Models</h5></v-card-title>
    <site-list-header v-model="filter" />
    <div class="proposal-list">
      <v-virtual-scroll
        ref="virtualList"
        height="calc(100vh - 150px)"
        :items="modifiedList"
        item-height="105"
      >
        <template #default="{item}">
          <site-list-card
            :key="item.id"
            :site="item"
            @click="selectSite(item)"
            @image-download="setImageDownloadDialog($event)"
            @cancel-download="cancelDownload()"
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


.proposal-list {
  position: sticky;
  top: 0px;
  z-index: 2;
  background-color: white;
  overflow-y: auto;
  max-height: calc(100vh - 150px);
}

</style>
