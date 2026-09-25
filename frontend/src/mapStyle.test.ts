import { describe, expect, it } from "vitest";
import { BASEMAP_STYLE, OPENSTREETMAP_TILE_URL } from "./mapStyle";

describe("basemap style", () => {
  it("uses the standard OpenStreetMap raster endpoint with attribution", () => {
    expect(OPENSTREETMAP_TILE_URL).toBe(
      "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    );
    expect(BASEMAP_STYLE.sources.openstreetmap).toMatchObject({
      type: "raster",
      tiles: [OPENSTREETMAP_TILE_URL],
      tileSize: 256,
      maxzoom: 19,
    });
    expect(BASEMAP_STYLE.sources.openstreetmap.attribution).toContain(
      "OpenStreetMap",
    );
  });
});
