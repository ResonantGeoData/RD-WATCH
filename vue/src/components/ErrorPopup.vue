<script setup lang="ts">
defineProps<{
  errorText: string
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text);
}
</script>

<template>
  <v-snackbar
    absolute
    multi-line
    location="top right"
    :model-value="!!errorText"
    vertical
    :timeout="-1"
    color="error"
  >
    <div class="mb-5">
      <span class="text-h5">An error has occurred.</span>
      <br>
      <span class="text-body-1">If you'd like to file a bug report, please copy the error trace below by clicking the copy button and include it in your report.</span>
    </div>
    <v-divider />
    <div class="d-flex">
      <div class="d-flex align-center mr-3">
        <v-tooltip
          text="Copy to clipboard"
          location="start"
        >
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              size="x-large"
              icon="mdi-content-copy"
              @click="copyToClipboard(errorText)"
            />
          </template>
        </v-tooltip>
      </div>
      <div
        class="overflow-auto"
        style="max-height: 40vh; white-space: pre-line;"
      >
        {{ errorText }}
      </div>
    </div>
    <template #actions>
      <v-btn
        color="info"
        variant="text"
        @click="emit('close')"
      >
        Close
      </v-btn>
    </template>
  </v-snackbar>
</template>
