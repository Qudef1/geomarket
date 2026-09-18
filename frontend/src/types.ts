export type Location = { latitude: number; longitude: number };
export type Components = Record<
  "competition" | "transport" | "target_audience" | "commercial_activity" | "centrality" | "amenities",
  number
>;
export type LocationScore = {
  score: number;
  grade: string;
  base_score: number;
  rule_adjustment: number;
  confidence: number;
  components: Components;
  positive_factors: string[];
  negative_factors: string[];
};
export type PointResponse = {
  location: Location;
  business_type: string;
  result: LocationScore;
  pois: Array<{ osm_id: string; category: string; location: Location; name?: string }>;
};
export type Candidate = { rank: number; location: Location; result: LocationScore };
export type SearchResult = Location & { display_name: string; type?: string };

