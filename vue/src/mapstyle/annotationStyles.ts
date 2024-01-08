import { DataDrivenPropertyValueSpecification, FormattedSpecification } from "maplibre-gl";
import { MapFilters } from "../store";

export type AnnotationStyle = Record<string, { color: string, type: string, label: string }>;

const defaultAnnotationColor = '#7F7F7F'

const defaultLabelText = '';

const styles: AnnotationStyle = {
  active_construction: {
    color: "#c00000",
    type: "observation",
    label: 'Active Construction',
  },
  post_construction: {
    color: "#5b9bd5",
    type: "observation",
    label: 'Post Construction',
  },
  site_preparation: {
    color: "#ffd966",
    type: "observation",
    label: 'Site Preparation',
  },
  unknown: {
    color: "#7030a0",
    type: "observation",
    label: 'Unknown',
  },
  no_activity: {
    color: "#a6a6a6",
    type: "observation",
    label: 'No Activity',
  },
  positive_annotated: {
    color: "#7f0000",
    type: "sites",
    label: 'Positive Annotated',
  },
  positive_partial: {
    color: "#00008b",
    type: "sites",
    label: 'Positive Partial',
  },
  positive_annotated_static: {
    color: "#ff8c00",
    type: "sites",
    label: 'Positive Annotated Static',
  },
  positive_partial_static: {
    color: "#ffff00",
    type: "sites",
    label: 'Positive Partial Static',
  },
  positive_pending: {
    color: "#1e90ff",
    type: "sites",
    label: 'Positive Pending',
  },
  positive_excluded: {
    color: "#00ffff",
    type: "sites",
    label: 'Positive Excluded',

  },
  negative: {
    color: "#ff00ff",
    type: "sites",
    label: 'Negative',
  },
  ignore: {
    color: "#00ff00",
    type: "sites",
    label: 'Ignore',
  },
  transient_positive: {
    color: "#ff69b4",
    type: "sites",
    label: 'Transient Positive',
  },
  transient_negative: {
    color: "#ffe4c4",
    type: "sites",
    label: 'Transient Negative',
  },
  system_proposed: {
    color: "#1F77B4",
    type: "sites",
    label: 'System Proposed',
  },
  system_confirmed: {
    color: "#1F77B4",
    type: "sites",
    label: 'System Confirmed',
  },
  system_rejected: {
    color: "#1F77B4",
    type: "sites",
    label: 'System Rejected',
  },
};

export type scoringColorsKeys = keyof typeof scoringColors;
const scoringColors = {
  2: {
    color: 'lime',
    title: 'True Positive (GT)',
    hex: '#2AFF00',
    description:'Positive site successfully detected (GT)',
    simple: true,
    detailed: true,
    id: 2,
  },
  3: {
    color: 'black',
    hex: '#000000',
    title: 'False Negative (GT)',
    description:'Positive site not detected (GT)',
    simple: true,
    detailed: true,
    id: 3,
  },
  5: {
    color: 'red',
    hex: '#FF0000',
    title: 'False Positive (GT)',
    description:'Negative annotation detected (GT)',
    simple: true,
    detailed: true,
    id: 5,
  },
  7: {
    color: 'thistle',
    hex: '#CAA7FF',
    title: 'Positive Site - Unbounded (GT)',
    description:'Positive site - incomplete activity (GT)',
    simple: false,
    detailed: true,
    id: 7,
  },
  10: {
    color: 'salmon',
    hex: '#FF8686',
    title: 'Ignore Area (GT)',
    description:'Ignore Area (GT)',
    simple: false,
    detailed: true,
    id: 10,
  },
  14: {
    color: 'lime',
    title: 'True Positive (GT)',
    hex: '#2AFF00',
    description:'Positive site successfully detected (GT)',
    simple: true,
    detailed: true,
    id: 14,
  },
  15: {
    color: 'black',
    hex: '#000000',
    title: 'False Negative (GT)',
    description:'Positive site not detected (GT)',
    simple: true,
    detailed: true,
    id: 15,
  },
  17: {
    hex: '#FF0000',
    title: 'False Positive (GT)',
    description:'Negative annotation detected (GT)',
    simple: true,
    detailed: true,
    id: 17,
  },
  19: {
    color: 'salmon',
    hex: '#FF8686',
    title: 'Ignore Area (GT)',
    description:'Ignore Area (GT)',
    simple: false,
    detailed: true,
    id: 19,
  },
  22: {
    color: 'magenta',
    hex: '#D53FFF',
    title: 'False Positive (Proposal)',
    description:'False Positive (Proposal)',
    simple: true,
    detailed: true,
    id: 22,
  },
  23: {
    color: 'orange',
    title: 'Partial Positive (Proposal)',
    hex: '#FF9033',
    description:'Partial positive - Associates with both a positive site and a negative site (Proposal)',
    simple: false,
    detailed: true,
    id: 23,
  },
  24: {
    color: 'aquamarine',
    hex: '#33FFEF',
    title: 'True Positive (Proposal)',
    description:'True Positive (Proposal)',
    simple: false,
    detailed: true,
    id: 24,
  },
  25: {
    color: 'magenta',
    hex: '#D53FFF',
    title: 'False Positive (Proposal)',
    description:'False Positive (Proposal)',
    simple: false,
    detailed: true,
    id: 25,
  },
}

const getAnnotationColor = (filters: MapFilters, fillProposals?: 'site' | 'observations') => {
    const result = [];
    result.push('case');
    if (filters.scoringColoring) {
      Object.entries(scoringColors).forEach(([id, { hex }]) => {
        result.push(['==', ['get', 'color_code'], parseInt(id, 10)])
        result.push(hex)
      })
    } 
    if (filters.proposals && fillProposals) {  
      const idKey = fillProposals === 'site' ? 'id' : 'siteeval_id'
      result.push(['in', ['get', idKey], ['literal', filters.proposals.accepted]])
      result.push('green');
      result.push(['in', ['get', idKey], ['literal', filters.proposals.rejected]])
      result.push('red');
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
    const scoringLegend: {color: string, name: string}[] = [];
    Object.values(scoringColors).forEach((data) => {
      if (scoringLegend.findIndex((item) => item.color === data.hex && item.name === data.title) === -1) {
          scoringLegend.push({ name: data.title, color: data.hex});
      }
    })
    return { observationLegend, scoringLegend, siteLegend }
}
const annotationLegend = createAnnotationLegend();

const getColorFromName = ((label: string) => {
 const vals = Object.values(styles);
 const found = vals.find((item) => item.label === label);
 return found?.color;
})

const getColorFromLabel = ((label: string) => styles[label]?.color || getColorFromName(label) || 'white');



export {
    annotationColors,
    observationText,
    annotationLegend,
    siteText,
    getColorFromLabel,
    styles,
    scoringColors,
}
