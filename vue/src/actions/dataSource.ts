import { state } from '../store';
import Router from '../router';
import { ApiService } from '../client';

const ALLOWED_DATA_SOURCES = ['scoring'];
const LOCAL_STORAGE_KEY = 'databaseSource';

function updateRoute(from: string | null, to: string | null) {
  const fromPrefix = from?.length ? `/${from}` : null;
  const toPrefix = to?.length ? `/${to}` : null;

  const fullPath = Router.currentRoute.value.fullPath;
  let target = fullPath;

  if (fromPrefix && target.startsWith(fromPrefix)) {
    target = target.slice(fromPrefix.length);
  }

  target = target.startsWith('/') ? target : `/${target}`;

  if (toPrefix && !target.startsWith(toPrefix)) {
    target = `${toPrefix}${target}`;
  }

  if (target !== fullPath) {
    Router.push(target);
  }
}

function persistSetting() {
  if (state.dataSource) {
    localStorage.setItem(LOCAL_STORAGE_KEY, state.dataSource);
  } else {
    localStorage.removeItem(LOCAL_STORAGE_KEY);
  }
}

function updateApiService() {
  const isScoringRoute = state.dataSource === 'scoring';

  // Set the ApiService prefix URL accordingly
  ApiService.setApiPrefix(isScoringRoute ? "/api/scoring" : "/api");
}

export function initializeDataSourceConfig() {
  // first read from URL
  const dataSource = ALLOWED_DATA_SOURCES.find(
    (src) => Router.currentRoute.value.fullPath.startsWith(`/${src}`)
  );

  if (dataSource) {
    setDataSource(dataSource);
  } else {
    // fallback to local storage
    const storageValue = localStorage.getItem(LOCAL_STORAGE_KEY)?.toLowerCase() ?? null;
    setDataSource(storageValue);
  }
}

export function setDataSource(db: string | null, options?: { persist?: boolean }) {
  if (db && !ALLOWED_DATA_SOURCES.includes(db)) {
    throw new Error(`DB ${db} is not supported`)
  }

  const oldDataSource = state.dataSource;
  state.dataSource = db;

  updateRoute(oldDataSource, db);
  updateApiService();

  const persist = options?.persist ?? false;
  if (persist) {
    persistSetting();
  }
}
