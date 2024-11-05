import { type InjectionKey, inject, reactive, readonly } from "vue";
import { ApiService } from "../client";
import { IQRSessionInfo } from "../client/services/ApiService";

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
  results: Array<[string, number]>;
}>({
  sessionId: null,
  sessionInfo: null,
  site: null,
  positives: new Set(),
  negatives: new Set(),
  results: [],
});

export function useIQR() {
  const iqrEnabled = inject(IQR_KEY, false);

  const setPrimarySite = (site: Site | null) => {
    state.site = site;
  };

  const refine = async () => {
    if (!state.sessionId) throw new Error('No active session');
    await ApiService.iqrRefine(state.sessionId);
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
  }

  const initializeSession = async () => {
    if (!state.site) throw new Error('No selected site');
    const result = await ApiService.iqrInitialize(state.sessionId, state.site.smqtkUuid);
    if (!result.success) throw new Error('Could not initialize IQR session');

    const sid = result.sid;
    state.sessionId = sid;

    await refine();
    await refreshSessionInfo();
    await refreshResults();
  };

  return {
    enabled: iqrEnabled,
    setPrimarySite,
    initializeSession,
    refine,
    refreshSessionInfo,
    state: readonly(state),
  };
}
