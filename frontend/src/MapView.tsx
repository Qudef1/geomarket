import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import type { GeoJSONSource, Map, MapMouseEvent } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { BASEMAP_STYLE } from "./mapStyle";
import type { Candidate, Location, PointResponse } from "./types";

type Props = {
  selected: Location;
  result: PointResponse | null;
  candidates: Candidate[];
  onSelect: (location: Location) => void;
  onBounds: (bounds: { south: number; west: number; north: number; east: number }) => void;
};

const empty = { type: "FeatureCollection" as const, features: [] };

export function MapView({ selected, result, candidates, onSelect, onBounds }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const onSelectRef = useRef(onSelect);
  const onBoundsRef = useRef(onBounds);
  onSelectRef.current = onSelect;
  onBoundsRef.current = onBounds;

  useEffect(() => {
    if (!container.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      style: BASEMAP_STYLE,
      center: [selected.longitude, selected.latitude],
      zoom: 13,
    });
    map.addControl(new maplibregl.NavigationControl(), "bottom-right");
    map.on("click", (event: MapMouseEvent) => onSelectRef.current({ latitude: event.lngLat.lat, longitude: event.lngLat.lng }));
    map.on("moveend", () => {
      const bounds = map.getBounds();
      onBoundsRef.current({ south: bounds.getSouth(), west: bounds.getWest(), north: bounds.getNorth(), east: bounds.getEast() });
    });
    map.on("load", () => {
      map.addSource("analysis", { type: "geojson", data: empty });
      map.addLayer({
        id: "analysis-heat", type: "heatmap", source: "analysis", maxzoom: 16,
        paint: {
          "heatmap-weight": ["coalesce", ["get", "score"], 0.4],
          "heatmap-intensity": 1.2,
          "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"], 0, "rgba(16,44,38,0)", 0.35, "#ee6c4d", 0.65, "#f5c451", 1, "#56c596"],
          "heatmap-radius": 34,
          "heatmap-opacity": 0.72,
        },
      });
      map.addLayer({ id: "analysis-points", type: "circle", source: "analysis", minzoom: 13.5, paint: { "circle-radius": 5, "circle-color": "#d9fff4", "circle-stroke-color": "#102c26", "circle-stroke-width": 2 } });
    });
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      const features = candidates.length
        ? candidates.map((candidate) => ({ type: "Feature" as const, properties: { score: candidate.result.score }, geometry: { type: "Point" as const, coordinates: [candidate.location.longitude, candidate.location.latitude] } }))
        : result?.pois.map((poi) => ({ type: "Feature" as const, properties: { score: 0.45 }, geometry: { type: "Point" as const, coordinates: [poi.location.longitude, poi.location.latitude] } })) ?? [];
      (map.getSource("analysis") as GeoJSONSource | undefined)?.setData({ type: "FeatureCollection", features });
    };
    map.isStyleLoaded() ? update() : map.once("load", update);
  }, [result, candidates]);

  useEffect(() => { mapRef.current?.easeTo({ center: [selected.longitude, selected.latitude], duration: 700 }); }, [selected]);
  return <div className="map" ref={container} aria-label="Interactive analysis map" />;
}
