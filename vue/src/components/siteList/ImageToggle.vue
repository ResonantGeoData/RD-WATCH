<script setup lang="ts">
import { ApiService } from "../../client/services/ApiService";
import { state } from "../../store";
const openNewTab = (id: string) => {
  const name = `#${ApiService.getApiPrefix().replace('api/','').replace('/api','')}/imageViewer/${id}`
  window.open(name, '_blank');
};


const props = defineProps<{
    imagesActive: boolean;
    hasImages: boolean;
    siteId: string;
    siteName: string;
}>();
const emit = defineEmits<{
    (e: "site-toggled"): void;
    (e: "image-browser-new-tab"): void;
}>();

const openImageBrowser = () => {
  state.selectedImageSite = {
    siteId: props.siteId,
    siteName: props.siteName,
  };
}


</script>

<template>
  <v-menu
    open-on-hover
    open-delay="600"
  >
    <template #activator="{ props }">
      <v-btn
        variant="tonal"
        density="compact"
        class="pa-0 ma-1 site-icon"
        size="small"
        :color="imagesActive ? 'success': ''"
        v-bind="props"
        @click.stop="hasImages && emit('site-toggled')"
      >
        <v-icon size="small">
          mdi-image
        </v-icon>
      </v-btn>
    </template>
    <v-list>
      <v-list-item @click="hasImages && openImageBrowser()">
        <v-list-item-title>
          Open Image Browser
        </v-list-item-title>
      </v-list-item>
      <v-list-item @click="hasImages && openNewTab(siteId)">
        <v-list-item-title>
          Open Image Browser (new tab)
        </v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
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
