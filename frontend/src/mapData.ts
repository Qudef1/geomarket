import type { Candidate, Location, PointResponse } from "./types";

export function selectedPointData(location: Location) {
  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        properties: { kind: "base-point" },
        geometry: {
          type: "Point" as const,
          coordinates: [location.longitude, location.latitude],
        },
      },
    ],
  };
}

export function analysisMapData(
  result: PointResponse | null,
  candidates: Candidate[],
) {
  const features = candidates.length
    ? candidates.map((candidate) => ({
        type: "Feature" as const,
        properties: {
          kind: "candidate",
          label: `Candidate #${candidate.rank}`,
          rank: candidate.rank,
          score: candidate.result.score,
          grade: candidate.result.grade,
        },
        geometry: {
          type: "Point" as const,
          coordinates: [
            candidate.location.longitude,
            candidate.location.latitude,
          ],
        },
      }))
    : (result?.pois.map((poi) => ({
        type: "Feature" as const,
        properties: {
          kind: "poi",
          label: poi.name ?? poi.category.replaceAll("_", " "),
          category: poi.category,
          osmId: poi.osm_id,
          score: 0.4,
        },
        geometry: {
          type: "Point" as const,
          coordinates: [poi.location.longitude, poi.location.latitude],
        },
      })) ?? []);

  return { type: "FeatureCollection" as const, features };
}
