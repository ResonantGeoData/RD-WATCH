import { type InjectionKey, computed, inject, reactive, readonly } from "vue";
import { ApiService, CancelablePromise } from "../client";
import { IQROrderedResultItem, IQRSessionInfo } from "../client/services/ApiService";

export const IQR_KEY: InjectionKey<boolean> = Symbol('IQR_KEY');

export type Site = {
  name: string;
  id: string;
  modelRunId?: string;
  smqtkUuid: string;
}

const internalState: {
  siteImageUrlPromise: CancelablePromise<string | null> | null;
} = {
  siteImageUrlPromise: null,
}

const state = reactive<{
  sessionId: string | null;
  sessionInfo: Omit<IQRSessionInfo, 'success'> | null;
  site: Site | null;
  siteImageUrl: string | null;
  positives: Set<string>;
  negatives: Set<string>;
  results: Array<IQROrderedResultItem>;
  refreshing: boolean;
  initializing: boolean;
}>({
  sessionId: null,
  sessionInfo: null,
  site: null,
  siteImageUrl: null,
  positives: new Set(),
  negatives: new Set(),
  results: [],
  refreshing: false,
  initializing: false,
});

function getUuidStatus(uuid: string): 'positive' | 'neutral' | 'negative' {
  if (state.positives.has(uuid)) return 'positive';
  if (state.negatives.has(uuid)) return 'negative';
  return 'neutral';
}

function clearResults() {
  state.results = [];
}

export function useIQR() {
  const iqrEnabled = inject(IQR_KEY, false);

  const setPrimarySite = (site: Site | null) => {
    state.site = site;
    internalState.siteImageUrlPromise?.cancel();
    if (site) {
      const promise = ApiService.iqrGetSiteImageUrl(site.id);
      promise.then((url) => {
        state.siteImageUrl = url;
      });
      internalState.siteImageUrlPromise = promise;
    } else {
      internalState.siteImageUrlPromise = null;
      clearResults();
    }
  };

  const refine = async () => {
    if (!state.sessionId) throw new Error('No active session');
    await ApiService.iqrRefine(state.sessionId);
  };

  const adjudicate = async (adjudications: Array<{ uuid: string, status: 'positive' | 'neutral' | 'negative' }>) => {
    if (!state.sessionId) throw new Error('No active session');
    await ApiService.iqrAdjudicate(state.sessionId, adjudications);

    const positives = new Set(state.positives);
    const negatives = new Set(state.negatives);

    adjudications.forEach((entry) => {
      positives.delete(entry.uuid);
      negatives.delete(entry.uuid);

      if (entry.status === 'positive') {
        positives.add(entry.uuid);
      } else if (entry.status === 'negative') {
        negatives.add(entry.uuid);
      }
    });

    state.positives = positives;
    state.negatives = negatives;
  };

  const refreshSessionInfo = async () => {
    if (!state.sessionId) throw new Error('No active session');
    state.sessionInfo = await ApiService.iqrGetSessionInfo(state.sessionId);
    state.positives = new Set(state.sessionInfo.uuids_pos);
    state.negatives = new Set(state.sessionInfo.uuids_neg);
  };

  const refreshResults = async () => {
    if (!state.sessionId) throw new Error('No active session');
    const result = await ApiService.iqrGetOrderedResults(state.sessionId);
    state.results = result.results;
  };

  const refineAndRefresh = async () => {
    if (state.refreshing) return;
    try {
      state.refreshing = true;
      await refine();
      await refreshSessionInfo();
      await refreshResults();
    } finally {
      state.refreshing = false;
    }
  };

  const initializeSession = async () => {
    if (state.initializing) return;
    if (!state.site) throw new Error('No selected site');

    try {
      state.initializing = true;

      const result = await ApiService.iqrInitialize(state.sessionId, state.site.smqtkUuid);
      if (!result.success) throw new Error('Could not initialize IQR session');

      const sid = result.sid;
      state.sessionId = sid;
    } finally {
      state.initializing = false;
    }

    await refineAndRefresh();
  };

  return {
    enabled: iqrEnabled,
    setPrimarySite,
    initializeSession,
    refine: refineAndRefresh,
    refreshSessionInfo,
    adjudicate,
    state: readonly(state),
    queryResults: computed(() => {
      return state.results.map((result) => {
        return {
          pk: result.pk,
          siteUid: result.site_uid,
          siteId: result.site_id,
          imageUrl: result.image_url,
          smqtkUuid: result.smqtk_uuid,
          status: getUuidStatus(result.smqtk_uuid),
          confidence: result.confidence,
          geomExtent: result.geom_extent,
        };
      });
    }),
  };
}
