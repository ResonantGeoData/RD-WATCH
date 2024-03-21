import { Tensor } from "onnxruntime-web";

export interface modelScaleProps {
  samScale: number;
  height: number;
  width: number;
}

export interface modelInputProps {
  x: number;
  y: number;
  hoverType: number;
}

export interface modeDataProps {
  hovered?: Array<modelInputProps>;
  tensor: Tensor;
  modelScale: modelScaleProps;
}

export interface ToolProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  handleMouseMove: (e: any) => void;
}
