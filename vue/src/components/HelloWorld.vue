<script setup lang="ts">
import { ref } from "vue";
import { useStatus } from "../composables/client/status";

defineProps<{ msg: string }>();

const count = ref(0);
const status = useStatus();
</script>

<template>
  <div class="grid h-screen items-center justify-center text-center">
    <div>
      <h1 class="text-4xl">{{ msg }}</h1>
    </div>
    <div>
      <img class="mx-auto w-96" src="../assets/world.svg" alt="Planet Earth" />
    </div>
    <div>
      <p v-if="status.data.value !== null">
        Connected to Django at
        <code>{{ status.data.value.hostname }}</code> (<code>{{
          status.data.value.ip
        }}</code
        >). It's been online for {{ status.data.value.uptime.days }} days,
        {{ status.data.value.uptime.seconds }} seconds, and
        {{ status.data.value.uptime.useconds }} µseconds.
      </p>
      <p v-else>Django service isn't alive :(</p>
    </div>
    <div>
      <button class="w-64 rounded bg-sky-500 py-5 text-white" @click="count++">
        count is {{ count }}
      </button>
    </div>
    <div>
      <p>
        Edit
        <code>components/HelloWorld.vue</code> to test HMR
      </p>
    </div>
  </div>
</template>
