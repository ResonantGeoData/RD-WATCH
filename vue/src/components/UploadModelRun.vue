<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import S3FileFieldClient, {
  S3FileFieldResultState,
} from "django-s3-file-field";
import { ApiService } from "../client";

const emits = defineEmits(['upload']);

const s3ffClient = new S3FileFieldClient({
  baseUrl: `${ApiService.getApiPrefix()}/s3-upload/`,
  apiConfig: {
    // django csrf token handling
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken",
  },
});

const modelRun = reactive({
  title: "",
  region: "",
  performer: "",
  private: false,
});

const successDialog = ref(false);
const uploadDialog = ref(false);
const validForm = ref(false);
const uploadFile = ref<File | File[]>();
const uploadLoading = ref(false);
const uploadError = ref<unknown>();
// Infinity means indeterminate
const uploadProgress = ref<number>(0);

const QUERY_TASK_POLL_DELAY = 1000; // msec
// from celery.states.READY_STATES
const CELERY_READY_STATES = ["FAILURE", "SUCCESS", "REVOKED"];

function resetModelRun() {
  modelRun.title = "";
  modelRun.region = "";
  modelRun.performer = "";
  modelRun.private = false;
  uploadFile.value = undefined;
}

watch(uploadDialog, (visible) => {
  if (!visible) return;
  resetModelRun();
})

function openUploadDialog() {
  uploadDialog.value = true;
  uploadFile.value = undefined;
  uploadError.value = undefined;
}

async function untilTaskReady(taskId: string) {
  return new Promise((resolve) => {
    async function queryTask() {
      const result = await ApiService.getModelRunUploadTaskStatus(taskId);

      if (CELERY_READY_STATES.includes(result)) {
        resolve(result);
      } else {
        setTimeout(() => {
          queryTask();
        }, QUERY_TASK_POLL_DELAY);
      }
    }

    queryTask();
  });
}

async function upload() {
  try {
    uploadLoading.value = true;
    uploadError.value = undefined;
    uploadProgress.value = Infinity;

    const file = Array.isArray(uploadFile.value)
      ? uploadFile.value[0]
      : uploadFile.value;
    if (!file) return;

    const uploadResult = await s3ffClient.uploadFile(
      file,
      "core.ModelRunUpload.zipfile"
    );
    if (uploadResult.state !== S3FileFieldResultState.Successful) {
      const status = ["was aborted", "", "errored"][uploadResult.state];
      throw new Error(`File upload ${status}`);
    }

    const taskId = await ApiService.postModelRunUpload({
      title: modelRun.title.trim(),
      region: modelRun.region.trim(),
      performer: modelRun.performer.trim(),
      zipfileKey: uploadResult.value,
      private: modelRun.private,
    });

    const taskState = await untilTaskReady(taskId);
    if (taskState !== "SUCCESS") {
      throw new Error(`Upload failed with state: ${taskState}`);
    }

    successDialog.value = true;
    emits('upload');
  } catch (err) {
    uploadError.value = err;
  } finally {
    uploadLoading.value = false;
  }
}

function validateTitle(title: string) {
  if (title.trim().length === 0) return "Must add a title";
  return true;
}

function validateFile(file: File | File[] | undefined) {
  if ((Array.isArray(file) && file.length !== 1) || !file)
    return "Must provide a model run file";
  return true;
}

function closeDialogs() {
  successDialog.value = false;
  uploadDialog.value = false;
}
</script>

<template>
  <v-btn
    color="light-blue-lighten-4"
    @click="openUploadDialog"
  >
    Upload Model Run
  </v-btn>
  <v-dialog
    v-model="uploadDialog"
    width="70%"
    persistent
  >
    <v-card>
      <v-card-title>Upload a new model run</v-card-title>
      <v-card-text>
        <v-form v-model="validForm">
          <v-text-field
            v-model="modelRun.title"
            label="Model Run Title"
            :rules="[validateTitle]"
            required
            :disabled="uploadLoading"
          />
          <v-file-input
            v-model="uploadFile"
            required
            clearable
            label="Model Run .zip file"
            :rules="[validateFile]"
            :disabled="uploadLoading"
          />
          <v-text-field
            v-model="modelRun.region"
            label="Override Region (optional)"
            :disabled="uploadLoading"
          />
          <v-text-field
            v-model="modelRun.performer"
            label="Override Performer (optional)"
            :disabled="uploadLoading"
          />
          <v-checkbox
            v-model="modelRun.private"
            label="Mark as private"
            :disabled="uploadLoading"
          />
          <v-alert
            v-if="uploadError"
            color="error"
          >
            {{ String(uploadError) }}
          </v-alert>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn
          :disabled="uploadLoading"
          @click="uploadDialog = false"
        >
          Cancel
        </v-btn>
        <v-btn
          :loading="uploadLoading"
          :disabled="!validForm || !uploadDialog"
          color="primary"
          variant="tonal"
          @click="upload"
        >
          Upload
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
  <v-dialog
    v-model="successDialog"
    persistent
    width="25%"
  >
    <v-card>
      <v-card-title>Upload Successful</v-card-title>
      <v-card-text>
        The model run has been successfully uploaded.
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="closeDialogs">
          OK
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
