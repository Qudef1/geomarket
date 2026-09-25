import { describe, expect, it } from "vitest";
import { analysisMapData, selectedPointData } from "./mapData";
import type { Candidate, PointResponse } from "./types";

const result: PointResponse = {
  location: { latitude: 60.17, longitude: 24.94 },
  business_type: "coffee_shop",
  result: {
    score: 0.78,
    grade: "high",
    base_score: 0.74,
    rule_adjustment: 0.04,
    confidence: 0.81,
    components: {
      competition: 0.5,
      transport: 0.9,
      target_audience: 0.8,
      commercial_activity: 0.7,
      centrality: 0.9,
      amenities: 0.6,
    },
    positive_factors: [],
    negative_factors: [],
  },
  pois: [
    {
      osm_id: "node/1",
      category: "university",
      location: { latitude: 60.171, longitude: 24.941 },
      name: "Example University",
    },
  ],
};

describe("map data", () => {
  it("places the selected base point at longitude-latitude coordinates", () => {
    expect(selectedPointData(result.location).features[0].geometry.coordinates).toEqual([
      24.94,
      60.17,
    ]);
  });

  it("turns point-analysis evidence into named map markers", () => {
    const data = analysisMapData(result, []);
    expect(data.features).toHaveLength(1);
    expect(data.features[0]).toMatchObject({
      properties: {
        kind: "poi",
        label: "Example University",
        category: "university",
      },
      geometry: { coordinates: [24.941, 60.171] },
    });
  });

  it("turns ranked results into scored candidate markers", () => {
    const candidates: Candidate[] = [
      { rank: 1, location: result.location, result: result.result },
    ];
    const data = analysisMapData(null, candidates);
    expect(data.features[0]).toMatchObject({
      properties: { kind: "candidate", rank: 1, score: 0.78 },
    });
  });
});
