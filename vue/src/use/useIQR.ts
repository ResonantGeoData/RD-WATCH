import { type InjectionKey, computed, inject, reactive, readonly, triggerRef } from "vue";
import { ApiService } from "../client";
import { IQROrderedResultItem, IQRSessionInfo } from "../client/services/ApiService";

export const IQR_KEY: InjectionKey<boolean> = Symbol('IQR_KEY');

export type Site = {
  name: string;
  id: string;
  modelRunId?: string;
  smqtkUuid: string;
}

const state = reactive<{
  sessionId: string | null;
  sessionInfo: Omit<IQRSessionInfo, 'success'> | null;
  site: Site | null;
  positives: Set<string>;
  negatives: Set<string>;
  results: Array<IQROrderedResultItem>;
}>({
  sessionId: null,
  sessionInfo: null,
  site: null,
  positives: new Set(),
  negatives: new Set(),
  results: [],
});

function getUuidStatus(uuid: string): 'positive' | 'neutral' | 'negative' {
  if (state.positives.has(uuid)) return 'positive';
  if (state.negatives.has(uuid)) return 'negative';
  return 'neutral';
}

export function useIQR() {
  const iqrEnabled = inject(IQR_KEY, false);

  const setPrimarySite = (site: Site | null) => {
    state.site = site;
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
    await refine();
    await refreshSessionInfo();
    await refreshResults();
  };

  const initializeSession = async () => {
    if (!state.site) throw new Error('No selected site');
    const result = await ApiService.iqrInitialize(state.sessionId, state.site.smqtkUuid);
    if (!result.success) throw new Error('Could not initialize IQR session');

    const sid = result.sid;
    state.sessionId = sid;

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
          siteId: result.site_id,
          smqtkUuid: result.smqtk_uuid,
          status: getUuidStatus(result.smqtk_uuid),
          confidence: result.confidence,
        };
      });
    }),
  };
}
