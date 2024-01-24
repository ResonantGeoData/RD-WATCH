import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { area as turfArea } from '@turf/turf';
import { Map } from "maplibre-gl";
import { Ref, ShallowRef, ref, shallowRef } from "vue";

export interface EditPolygonType {
    initialize: () => void;
    setPolygonEdit: (polygon: GeoJSON.Polygon) => void

}

export default function useEditPolygon(mapObj: Map): EditPolygonType {
    const map: ShallowRef<Map> = shallowRef(mapObj);
    const draw: Ref<MapboxDraw | null> = ref(null);
    MapboxDraw.constants.classes.CONTROL_BASE  = 'maplibregl-ctrl';
    MapboxDraw.constants.classes.CONTROL_PREFIX = 'maplibregl-ctrl-';
    MapboxDraw.constants.classes.CONTROL_GROUP = 'maplibregl-ctrl-group';

    const created = (e: MapboxDraw.DrawEvent) => {
        console.log('element created')
        console.log(e);
    };
    const deleted = (e: MapboxDraw.DrawEvent) => {
        console.log('element deleted')
        console.log(e);
    };
    const updated = (e: MapboxDraw.DrawEvent) => {
        console.log('element updated')
        console.log(e);
    };
    const modeChanged = (e: MapboxDraw.DrawEvent) => {
        console.log('mode changed')
        console.log(e);
    };
    const render = (e: MapboxDraw.DrawEvent) => {
        console.log('draw render')
        console.log(e);
        console.log(map.value);
        console.log(map.value.getStyle().layers);
    };

    const selectionChange = (e: MapboxDraw.DrawEvent) => {
        console.log('selection change')
        console.log(e);
    };

    const initialize = () => {
    if (draw.value) {
        map.value.removeControl(draw.value);
    }
    draw.value = new MapboxDraw({
        displayControlsDefault: true,
        controls: {
            polygon: true,
            trash: true
        },
        // styles: [
        //     {
        //       'id': 'highlight-active-points',
        //       'type': 'circle',
        //       'filter': ['all',
        //         ['==', '$type', 'Point'],
        //         ['==', 'meta', 'feature'],
        //         ['==', 'active', 'true']],
        //       'paint': {
        //         'circle-radius': 7,
        //         'circle-color': '#000000'
        //       }
        //     },
        //     {
        //       'id': 'points-are-blue',
        //       'type': 'circle',
        //       'filter': ['all',
        //         ['==', '$type', 'Point'],
        //         ['==', 'meta', 'feature'],
        //         ['==', 'active', 'false']],
        //       'paint': {
        //         'circle-radius': 5,
        //         'circle-color': '#000088'
        //       }
        //     }
        //   ]
    });
    map.value.addControl(draw.value, 'top-right');


    map.value.on('draw.create', created);
    map.value.on('draw.delete', deleted);
    map.value.on('draw.update', updated);
    map.value.on('draw.selectionchange', selectionChange);
    map.value.on('draw.modechange', modeChanged);
    map.value.on('draw.render', render);
    };

    const setPolygonEdit = (polygon: GeoJSON.Polygon) => {
        console.log(draw.value);
        if (draw.value) {
            const featureIds = draw.value.add(polygon);
            console.log(featureIds);
            console.log(draw.value.getMode());
            console.log(draw.value.changeMode('direct_select', { featureId: featureIds[0]}));
        }
    }

    return {
        initialize,
        setPolygonEdit,
    }

}