import { afterEach, describe, expect, it, vi } from "vitest";
import { analyzePoint, searchPlaces } from "./api";

afterEach(() => vi.restoreAllMocks());

describe("API client", () => {
  it("encodes search text", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([]), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    await searchPlaces("Kamppi Helsinki");
    expect(fetchMock.mock.calls[0][0]).toContain("Kamppi%20Helsinki");
  });

  it("sends a typed coffee shop point request", async () => {
    const payload = { location: { latitude: 60.17, longitude: 24.94 }, business_type: "coffee_shop", result: {}, pois: [] };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    await analyzePoint({ latitude: 60.17, longitude: 24.94 });
    const options = fetchMock.mock.calls[0][1];
    expect(JSON.parse(String(options?.body))).toMatchObject({ business_type: "coffee_shop", radius_m: 1000 });
  });
});

