<script setup lang="ts">
import { Ref, defineProps, onMounted, onUnmounted, ref } from "vue";
import {
  ApiService,
  DownloadedAnimation,
} from "../../client/services/ApiService";
import { downloadPresignedFile } from "../../utils";

const props = defineProps<{
  type: "site" | "modelRun";
  id: string;
}>();

const currentList: Ref<DownloadedAnimation[]> = ref([]);

const dateOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false, // Set to false if you prefer a 24-hour format
  };

let timeoutVal: NodeJS.Timeout | null = null;

const formatDateTime = (timeString: string) => {
  // Create a Date object from the time string
  const date = new Date(timeString);

  // Convert to human-readable format
  return date.toLocaleString("en-US", dateOptions);
}

const expiredTime = (timeString: string) => {
    const date = new Date(timeString);
    const addHours = props.type === 'site' ? 6 : 48;
    const addTime = addHours * 60 *60 * 1000;
    const expirdeDate = new Date(date.getTime() + addTime);
    return expirdeDate.toLocaleString("en-US", dateOptions);
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
    if (timeoutVal !== null) {
      clearTimeout(timeoutVal)
      timeoutVal = null;
    }
    timeoutVal = setTimeout(checkDownloadStatus, 1000);
  }
};
const initialized = ref(false);
onMounted(async () => {
    initialized.value = false;
    await checkDownloadStatus();
    initialized.value = true;
});

onUnmounted(() => {
  if (timeoutVal !== null) {
      clearTimeout(timeoutVal)
    }
})

const downloadItem = async (taskId: string) => {
  const { url, filename}  = await ApiService.getAnimationDownloadString(taskId, props.type);
  downloadPresignedFile(url, filename);
};

const deleteItem = async (taskId: string) => {
        const result = props.type === 'site' ? await ApiService.deleteAnimationSiteDownload(taskId): await ApiService.deleteAnimationModelRunDownload(taskId);
        if (result.success) {
            checkDownloadStatus();
        }
}

const cancelAnimation = async (taskId: string) => {
  const result = await ApiService.cancelAnimationDownload(taskId);
  if (result.success) {
    checkDownloadStatus();
  }
}

const headers = ref([
  { title: "Date", key: "created", width: "250px" },
  { title: "Arguments", key: "arguments", width: "20px" },
  { title: "Status", value: "completed", width: "250px" },
]);
</script>

<template>
  <div>
    <v-row><h2>Animation Download Status</h2></v-row>
    <v-row>
      <p v-if="type === 'site'">
        Animation Downloads for Sites are removed automatically from the system after 6 hours.
      </p>
      <p v-if="type === 'modelRun'">
        Animation Downloads for ModelRuns are removed automatically from the system after 48 hours.
      </p>
    </v-row>
    <v-data-table-virtual
      v-if="currentList.length && initialized"
      :headers="headers"
      :items="currentList"
      height="700"
      item-value="key"
    >
      <template #[`item.created`]="{ item }">
        <v-row dense>
          <v-col cols="5">
            Created:
          </v-col><v-col><b>{{ formatDateTime(item.created) }}</b></v-col>
        </v-row>
        <v-row dense>
          <v-col cols="5">
            Expire:
          </v-col><v-col><b>{{ expiredTime(item.created) }}</b></v-col>
        </v-row>
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
          <v-row
            dense
            align="center"
            justify="center"
          >
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
            <v-row dense>
              <v-spacer />
              <v-btn
                size="x-small"
                color="error"
                @click="cancelAnimation(item.taskId)"
              >
                Cancel
              </v-btn>
              <v-spacer />
            </v-row>
          </div>
          <div v-else-if="item.state && item.state.error">
            <v-alert type="error">
              {{ item.state.error }}
            </v-alert>
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
            <v-row dense>
              <v-spacer />
              <v-btn
                size="x-small"
                color="error"
                @click="cancelAnimation(item.taskId)"
              >
                Cancel
              </v-btn>
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
