<script setup lang="ts">
import { state } from '../store';

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text);
}
</script>

<template>
  <v-dialog width="500">
    <template #activator="{ props }">
      <v-btn
        v-show="state.errorText"
        v-bind="props"
        icon="mdi-alert"
        location="top left"
        position="absolute"
        class="ma-4"
        :color="state.errorText ? 'warning' : 'default'"
        style="z-index: 2;"
        :disabled="!state.errorText"
      />
    </template>

    <template #default="{ isActive }">
      <v-card title="Error">
        <v-card-text>
          <div class="mb-5">
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
                    @click="copyToClipboard(state.errorText)"
                  />
                </template>
              </v-tooltip>
            </div>
            <div
              class="overflow-auto"
              style="max-height: 40vh; white-space: pre-line;"
            >
              {{ state.errorText }}
            </div>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />

          <v-btn
            text="Close"
            @click="isActive.value = false; state.errorText = ''"
          />
        </v-card-actions>
      </v-card>
    </template>
  </v-dialog>
</template>
