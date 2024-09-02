<script setup lang="ts">
import { Ref, defineProps, onMounted, ref } from "vue";
import {
  ApiService,
  DownloadedAnimation,
} from "../../client/services/ApiService";

const props = defineProps<{
  type: "site" | "modelRun";
  id: string;
}>();

const currentList: Ref<DownloadedAnimation[]> = ref([]);

function formatDateTime(timeString: string) {
  // Create a Date object from the time string
  const date = new Date(timeString);

  // Define formatting options
  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false, // Set to false if you prefer a 24-hour format
  };

  // Convert to human-readable format
  return date.toLocaleString("en-US", options);
}
const checkDownloadStatus = async () => {
  let checkAgain = false;
  if (props.type === "site") {
    const data = await ApiService.getAnimationSiteDownloaded(props.id);
    data.forEach((item) => {
      if (!item.completed) {
        checkAgain = true;
      }
    });
    currentList.value = data;
  } else if (props.type === "modelRun") {
    const data = await ApiService.getAnimationModelRunDownloaded(props.id);
    data.forEach((item) => {
      if (!item.completed) {
        checkAgain = true;
      }
    });
    currentList.value = data;
  }
  if (checkAgain) {
    setTimeout(checkDownloadStatus, 1000);
  }
};
const initialized = ref(false);
onMounted(async () => {
    initialized.value = false;
    await checkDownloadStatus();
    initialized.value = true;
});

const downloadItem = (taskId: string) => {
  const url = ApiService.getAnimationDownloadString(taskId, props.type);
  window.location.assign(url);
};

const deleteItem = async (taskId: string) => {
        const result = props.type === 'site' ? await ApiService.deleteAnimationSiteDownload(taskId): await ApiService.deleteAnimationModelRunDownload(taskId);
        if (result.success) {
            checkDownloadStatus();
        }
}
const headers = ref([
  { title: "Created", key: "created", width: "250px" },
  { title: "Arguments", key: "arguments", width: "20px" },
  { title: "Status", key: "completed" },
]);
</script>

<template>
  <div>
    <v-row><h2>Animation Download Status</h2></v-row>
    <v-data-table-virtual
      v-if="currentList.length && initialized"
      :headers="headers"
      :items="currentList"
      height="700"
      item-value="key"
    >
      <template #[`item.created`]="{ item }">
        <b>{{ formatDateTime(item.created) }}</b>
      </template>
      <template #[`item.arguments`]="{ item }">
        <div>
          <b>format:</b><span>{{ item.arguments.output_format }}</span>
        </div>
        <div>
          <b>fps:</b><span>{{ item.arguments.fps }}</span>
        </div>
        <div>
          <b>sources:</b><span>{{ item.arguments.sources.join(",") }}</span>
        </div>
        <div>
          <b>labels:</b><span>{{ item.arguments.labels.join(",") }}</span>
        </div>
      </template>
      <template #[`item.completed`]="{ item }">
        <div v-if="item.completed">
          <v-row dense>
            <v-btn @click="downloadItem(item.taskId)">
              Download <v-icon>mdi-download</v-icon>
            </v-btn>
            <v-spacer />
            <v-icon
              color="error"
              @click="deleteItem(item.taskId)"
            >
              mdi-delete
            </v-icon>
          </v-row>
        </div>
        <div v-else>
          <div v-if="item.state && item.state.info">
            <v-row dense>
              <v-progress-linear
                :model-value="item.state.info.current"
                :max="item.state.info.total"
                height="25"
              />
            </v-row>
            <v-row dense>
              <v-spacer />
              <div>{{ item.state.info.mode }}</div>
              <v-spacer />
            </v-row>
          </div>
          <div v-else>
            <v-row dense>
              <v-progress-linear
                indeterminate
                height="25"
              />
            </v-row>
            <v-row dense>
              <v-spacer />
              <div>Pending</div>
              <v-spacer />
            </v-row>
          </div>
        </div>
      </template>
    </v-data-table-virtual>
    <div
      v-else-if="initialized"
      class="pt-5"
    >
      <v-row dense>
        <v-alert color="warning">
          <h2>No Downloads have been created yet</h2>
        </v-alert>
      </v-row>
    </div>
  </div>
</template>
