import type { StyleSpecification } from "maplibre-gl";

export const OPENSTREETMAP_TILE_URL =
  "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

export const BASEMAP_STYLE = {
  version: 8,
  sources: {
    openstreetmap: {
      type: "raster",
      tiles: [OPENSTREETMAP_TILE_URL],
      tileSize: 256,
      maxzoom: 19,
      attribution:
        '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    },
  },
  layers: [
    {
      id: "openstreetmap",
      type: "raster",
      source: "openstreetmap",
    },
  ],
} satisfies StyleSpecification;
