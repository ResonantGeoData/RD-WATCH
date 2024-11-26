import { type FitBoundsOptions } from 'maplibre-gl';
import { type BoundingBox, createEventHook } from '../utils';

export const FitBoundsEvent = createEventHook<BoundingBox & FitBoundsOptions>();
