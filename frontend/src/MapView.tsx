import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import type { GeoJSONSource, Map, MapMouseEvent } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { analysisMapData, selectedPointData } from "./mapData";
import { BASEMAP_STYLE } from "./mapStyle";
import type { Candidate, Location, PointResponse } from "./types";

type Props = {
  selected: Location;
  result: PointResponse | null;
  candidates: Candidate[];
  onSelect: (location: Location) => void;
  onBounds: (bounds: { south: number; west: number; north: number; east: number }) => void;
};

const ANALYSIS_SOURCE = "analysis";
const ANALYSIS_POINTS_LAYER = "analysis-points";
const SELECTED_SOURCE = "selected-point-source";

maplibregl.setWorkerUrl("/assets/maplibre-gl-worker.mjs");

function showResultPopup(map: Map, event: MapMouseEvent): boolean {
  if (!map.getLayer(ANALYSIS_POINTS_LAYER)) return false;
  const [feature] = map.queryRenderedFeatures(event.point, {
    layers: [ANALYSIS_POINTS_LAYER],
  });
  if (!feature) return false;

  const properties = feature.properties as Record<string, unknown>;
  const content = document.createElement("div");
  content.className = "result-popup";
  const title = document.createElement("strong");
  title.textContent = String(properties.label ?? "Analysis result");
  const detail = document.createElement("span");
  detail.textContent =
    properties.kind === "candidate"
      ? `${Math.round(Number(properties.score) * 100)}/100 suitability`
      : String(properties.category ?? "point of interest").replaceAll("_", " ");
  content.append(title, detail);
  new maplibregl.Popup({ offset: 10 })
    .setLngLat(event.lngLat)
    .setDOMContent(content)
    .addTo(map);
  return true;
}

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
    map.getCanvas().style.cursor = "crosshair";
    map.on("click", (event: MapMouseEvent) => {
      if (showResultPopup(map, event)) return;
      onSelectRef.current({
        latitude: event.lngLat.lat,
        longitude: event.lngLat.lng,
      });
    });
    map.on("moveend", () => {
      const bounds = map.getBounds();
      onBoundsRef.current({ south: bounds.getSouth(), west: bounds.getWest(), north: bounds.getNorth(), east: bounds.getEast() });
    });
    map.on("load", () => {
      map.addSource(ANALYSIS_SOURCE, {
        type: "geojson",
        data: analysisMapData(result, candidates),
      });
      map.addLayer({
        id: "analysis-heat", type: "heatmap", source: ANALYSIS_SOURCE, maxzoom: 16,
        paint: {
          "heatmap-weight": ["coalesce", ["get", "score"], 0.4],
          "heatmap-intensity": 1.2,
          "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"], 0, "rgba(16,44,38,0)", 0.35, "#ee6c4d", 0.65, "#f5c451", 1, "#56c596"],
          "heatmap-radius": 28,
          "heatmap-opacity": 0.5,
        },
      });
      map.addLayer({
        id: ANALYSIS_POINTS_LAYER,
        type: "circle",
        source: ANALYSIS_SOURCE,
        paint: {
          "circle-radius": [
            "case",
            ["==", ["get", "kind"], "candidate"],
            ["interpolate", ["linear"], ["get", "score"], 0, 7, 1, 12],
            6,
          ],
          "circle-color": [
            "case",
            ["==", ["get", "kind"], "candidate"],
            ["interpolate", ["linear"], ["get", "score"], 0, "#ee6c4d", 0.5, "#f5c451", 1, "#55d6aa"],
            ["match", ["get", "category"], "cafe", "#ee6c4d", "restaurant", "#f5c451", "university", "#7c9cff", "bus_stop", "#55d6aa", "station", "#4bb8e8", "office", "#c38cff", "parking", "#a9b8b2", "supermarket", "#8bd17c", "#d9fff4"],
          ],
          "circle-opacity": 0.94,
          "circle-stroke-color": "#09201a",
          "circle-stroke-width": 2,
        },
      });
      map.addSource(SELECTED_SOURCE, {
        type: "geojson",
        data: selectedPointData(selected),
      });
      map.addLayer({
        id: "selected-point-halo",
        type: "circle",
        source: SELECTED_SOURCE,
        paint: {
          "circle-radius": 17,
          "circle-color": "rgba(85, 214, 170, 0.24)",
          "circle-stroke-color": "rgba(85, 214, 170, 0.65)",
          "circle-stroke-width": 2,
        },
      });
      map.addLayer({
        id: "selected-point",
        type: "circle",
        source: SELECTED_SOURCE,
        paint: {
          "circle-radius": 7,
          "circle-color": "#55d6aa",
          "circle-stroke-color": "#071713",
          "circle-stroke-width": 3,
        },
      });
      map.on("mouseenter", ANALYSIS_POINTS_LAYER, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", ANALYSIS_POINTS_LAYER, () => {
        map.getCanvas().style.cursor = "crosshair";
      });
    });
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      (map.getSource(ANALYSIS_SOURCE) as GeoJSONSource | undefined)?.setData(
        analysisMapData(result, candidates),
      );
    };
    map.getSource(ANALYSIS_SOURCE) ? update() : map.once("load", update);
  }, [result, candidates]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      (map.getSource(SELECTED_SOURCE) as GeoJSONSource | undefined)?.setData(
        selectedPointData(selected),
      );
      map.easeTo({ center: [selected.longitude, selected.latitude], duration: 500 });
    };
    map.getSource(SELECTED_SOURCE) ? update() : map.once("load", update);
  }, [selected]);

  return (
    <div className="map-shell">
      <div className="map" ref={container} aria-label="Interactive analysis map" />
      <div className="map-legend" aria-label="Map legend">
        <span><i className="base-point-key" />Base point</span>
        {result && <span><i className="evidence-key" />Evidence locations</span>}
        {candidates.length > 0 && <span><i className="candidate-key" />Ranked candidates</span>}
      </div>
    </div>
  );
}
