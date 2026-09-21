declare module "react-simple-maps" {
  import type { ComponentType, ReactNode, CSSProperties } from "react";

  export interface GeographyType {
    rsmKey: string;
    properties: Record<string, unknown>;
  }

  export const ComposableMap: ComponentType<{
    projection?: string;
    projectionConfig?: Record<string, unknown>;
    width?: number;
    height?: number;
    style?: CSSProperties;
    children?: ReactNode;
  }>;

  export const Geographies: ComponentType<{
    geography: string | object;
    children: (args: { geographies: GeographyType[] }) => ReactNode;
  }>;

  export const Geography: ComponentType<{
    geography: GeographyType;
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
    style?: {
      default?: CSSProperties;
      hover?: CSSProperties;
      pressed?: CSSProperties;
    };
  }>;
}
