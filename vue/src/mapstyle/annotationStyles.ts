import { DataDrivenPropertyValueSpecification, FormattedSpecification } from "maplibre-gl";
import { MapFilters } from "../store";

export interface AnnotationStyle {
    id: number;
    label: string;
    color: string;
    labelType: 'observation' | 'sites' | ''; // Filter for label types
}

const defaultAnnotationColor = '#7F7F7F'

const defaultLabelText = '';

const styles: AnnotationStyle[] = [
    {
        id: 1,
        color: '#007DFF',
        label: 'active_construction',
        labelType: 'observation',
    },
    {
        id: 2,
        color: '#BE4EFF',
        label: 'post_construction',
        labelType: 'observation',
    },
    {
        id: 3,
        color: '#FFA100',
        label: 'site_preparation',
        labelType: 'observation',
    },
    {
        id: 4,
        color: '#FFA100',
        label: '',
        labelType: ''
    },
    {
        id: 5,
        color: '#228b22',
        label: '',
        labelType: ''
    },
    {
        id: 6,
        color: '#7f0000',
        label: 'positive_annotated',
        labelType: 'sites'
    },
    {
        id: 7,
        color: '#00008b',
        label: 'positive_partial',
        labelType: 'sites',
    },
    {
        id: 8,
        color: '#ff8c00',
        label: 'positive_annotated_static',
        labelType: 'sites',
    },
    {
        id: 9,
        color: '#ffff00',
        label: 'positive_partial_static',
        labelType: 'sites',
    },
    {
        id: 10,
        color: '#1e90ff',
        label: 'positive_pending',
        labelType: 'sites',
    },
    {
        id: 11,
        color: '#00ffff',
        label: 'positive_excluded',
        labelType: 'sites',
    },
    {
        id: 12,
        color: '#ff00ff',
        label: 'negative',
        labelType: 'sites',
    },
    {
        id: 13,
        color: '#00ff00',
        label: 'ignore',
        labelType: 'sites',
    },
    {
        id: 14,
        color: '#ff69b4',
        label: 'transient_positive',
        labelType: 'sites',
    },
    {
        id: 15,
        color: '#ffe4c4',
        label: 'transient_negative',
        labelType: 'sites',
    },
    {
        id: 16,
        color: '#1F77B4',
        label: 'system_proposed',
        labelType: 'sites',
    },
    {
        id: 17,
        color: '#1F77B4',
        label: 'system_confirmed',
        labelType: 'sites',
    },
    {
        id: 18,
        color: '#1F77B4',
        label: 'system_rejected',
        labelType: 'sites',
    },
]

const getAnnotationColor = (filters: MapFilters) => {
    const result = [];
    result.push('case');
    //console.log(filters);
    if (filters.scoringColoring) {
        Object.entries(filters.scoringColoring).forEach(([key, value]) => {
            //console.log(`key:${key} - value: ${value}`);
            const splits = key.split('_').map((item) => parseInt(item));
            //console.log(splits);
            if (splits.length === 4) {
                result.push(['all',
                    ['==', ['get', 'configuration_id'], splits[0]],
                    ['==', ['get', 'region_id'], splits[1]],
                    ['==', ['get', 'performer_id'], splits[2]],
                    ['==', ['get', 'site_number'], splits[3]],
                ]);
                result.push(value);
            }
        });
    }
    styles.forEach((item) => {
        result.push(['==', ['get', 'label'], item.id]);
        result.push(item.color);
    });
    result.push(defaultAnnotationColor);
    //console.log(result);
    return result as DataDrivenPropertyValueSpecification<string>;
}

const getText = (textType: AnnotationStyle['labelType']) => {
    const result = [];
    result.push('case');
    styles.filter((item) => item.labelType === textType).forEach((item) => {
        result.push(['==', ['get', 'label'], item.id]);
        result.push(item.label);
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
    styles.forEach((item) => {
        if (item.labelType === 'observation'){
            observationLegend.push({color: item.color, name: item.label})
        }
        if (item.labelType === 'sites'){
            siteLegend.push({color: item.color, name: item.label})
        }
    });
    const scoringLegend = [
        { name:'Ignore', color:'lightsalmon' },
        { name:'Positive Match', color:'orange' },
        { name:'Partially Wrong', color:'aquamarine' },
        { name:'Completely Wrong', color:'magenta' },
    ]
    return { observationLegend, scoringLegend, siteLegend }
}
const annotationLegend = createAnnotationLegend();

export {
    annotationColors,
    observationText,
    annotationLegend,
    siteText,
}
