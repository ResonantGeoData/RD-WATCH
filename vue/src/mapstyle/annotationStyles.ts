import { DataDrivenPropertyValueSpecification, FormattedSpecification } from "maplibre-gl";
import { MapFilters } from "../store";

export type AnnotationStyle = Record<string, { color: string, type: string }>;

const defaultAnnotationColor = '#7F7F7F'

const defaultLabelText = '';

const styles: AnnotationStyle = {
  active_construction: {
    color: "#007DFF",
    type: "observation",
  },
  post_construction: {
    color: "#BE4EFF",
    type: "observation",
  },
  site_preparation: {
    color: "#FFA100",
    type: "observation",
  },
  unknown: {
    color: "#FFA100",
    type: "observation",
  },
  no_activity: {
    color: "#228b22",
    type: "observation",
  },
  positive_annotated: {
    color: "#7f0000",
    type: "sites",
  },
  positive_partial: {
    color: "#00008b",
    type: "sites",
  },
  positive_annotated_static: {
    color: "#ff8c00",
    type: "sites",
  },
  positive_partial_static: {
    color: "#ffff00",
    type: "sites",
  },
  positive_pending: {
    color: "#1e90ff",
    type: "sites",
  },
  positive_excluded: {
    color: "#00ffff",
    type: "sites",
  },
  negative: {
    color: "#ff00ff",
    type: "sites",
  },
  ignore: {
    color: "#00ff00",
    type: "sites",
  },
  transient_positive: {
    color: "#ff69b4",
    type: "sites",
  },
  transient_negative: {
    color: "#ffe4c4",
    type: "sites",
  },
  system_proposed: {
    color: "#1F77B4",
    type: "sites",
  },
  system_confirmed: {
    color: "#1F77B4",
    type: "sites",
  },
  system_rejected: {
    color: "#1F77B4",
    type: "sites",
  },
};

const getAnnotationColor = (filters: MapFilters) => {
    const result = [];
    result.push('case');
    if (filters.scoringColoring) {
        const baseScore = Object.values(filters.scoringColoring)
        baseScore.forEach((base) => {
            Object.entries(base).forEach(([key, value]) => {
                const splits = key.split('_').map((item) => parseInt(item));
                if (splits.length === 4) {
                    result.push(['all',
                        ['==', ['get', 'configuration_id'], splits[0]],
                        ['==', ['get', 'region'], splits[1]],
                        ['==', ['get', 'performer_id'], splits[2]],
                        ['==', ['get', 'site_number'], splits[3]],
                    ]);
                    result.push(value);
                }
            });
        });
    }
    Object.entries(styles).forEach(([label, { color }]) => {
        result.push(['==', ['get', 'label'], label]);
        result.push(color);
    });
    result.push(defaultAnnotationColor);
    return result as DataDrivenPropertyValueSpecification<string>;
}

const getText = (textType: string) => {
    const result = [];
    result.push('case');
    Object.entries(styles).filter(([, { type }]) => type === textType).forEach(([label,]) => {
        result.push(['==', ['get', 'label'], label]);
        result.push(label);
    })
    result.push(defaultLabelText);
    return result as DataDrivenPropertyValueSpecification<FormattedSpecification>;
}

const annotationColors = getAnnotationColor;
const observationText = getText('observation')
const siteText = getText('sites');

const createAnnotationLegend = () => {
    const observationLegend: {color: string, name: string}[] = [];
    const siteLegend: {color: string, name: string}[] = [];
    Object.entries(styles).forEach(([label, { type, color }]) => {
        if (type === 'observation'){
            observationLegend.push({color: color, name: label})
        }
        if (type === 'sites'){
            siteLegend.push({color: color, name: label})
        }
    });
    const scoringLegend = [
        { name:'Ignore', color:'lightsalmon' },
        { name:'Positive Match', color:'#66CCAA' },
        { name:'Partially Wrong', color:'orange' },
        { name:'Completely Wrong', color:'magenta' },
    ]
    return { observationLegend, scoringLegend, siteLegend }
}
const annotationLegend = createAnnotationLegend();

const getColorFromLabel = ((label: string) => styles[label].color);

export {
    annotationColors,
    observationText,
    annotationLegend,
    siteText,
    getColorFromLabel,
    styles,
}
