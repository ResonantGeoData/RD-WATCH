import { ref } from "vue";
import { ApiService } from "../../client";

import type { ServerStatus } from "../../client";
import type { Ref } from "vue";

export function useStatus() {
  const data: Ref<ServerStatus | null> = ref(null);

  ApiService.getStatus().then((json) => (data.value = json));

  return { data };
}
