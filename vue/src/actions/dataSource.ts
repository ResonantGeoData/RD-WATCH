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

export function reloadDataSourceFromStorage() {
  const storageValue = localStorage.getItem(LOCAL_STORAGE_KEY)?.toLowerCase() ?? null;
  setDataSource(storageValue);
}

export function setDataSource(db: string | null) {
  if (db && !ALLOWED_DATA_SOURCES.includes(db)) {
    throw new Error(`DB ${db} is not supported`)
  }

  const oldDataSource = state.dataSource;
  state.dataSource = db;

  persistSetting();
  updateRoute(oldDataSource, db);
  updateApiService();
}
