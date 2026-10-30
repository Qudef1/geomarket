# GeoMarket AI metrics and formulas

This document describes every numerical metric and formula currently used by GeoMarket AI and the
evaluation metrics explicitly planned for later ML work. It is the mathematical reference for the
current deterministic baseline.

The most important distinction is:

```text
Current system = deterministic heuristic score + explicit rule modifiers
Future system  = trained model evaluated against the deterministic baseline
```

The current score is not a probability of business success, estimated revenue, or a statistically
calibrated prediction. No trained model metrics are currently reported.

## 1. Notation

| Symbol | Meaning |
| --- | --- |
| `L` | Candidate location being evaluated |
| `P` | Set of normalized points of interest (POIs) |
| `d(a,b)` | Great-circle distance between locations `a` and `b`, in metres |
| `N(c,r)` | Count of POIs in category `c` within radius `r` of `L` |
| `clip(x,0,1)` | Restrict `x` to the inclusive interval `[0,1]` |
| `S(x,T)` | Saturation normalization of value `x` at threshold `T` |
| `B` | Deterministic baseline score |
| `A` | Sum of triggered rule adjustments |
| `F` | Final suitability score |
| `K` | Number of top ranked results requested |

All internal suitability and component scores use the range `0.0..1.0`. The frontend converts them
to `0..100` only for display.

## 2. Geographic formulas

Implementation: [`backend/app/services/geo.py`](../backend/app/services/geo.py).

### 2.1 Great-circle distance: Haversine formula

The application calculates in-memory distance between two latitude/longitude points with the
Haversine formula.

Given points `a = (lat1, lon1)` and `b = (lat2, lon2)`:

```text
phi1 = radians(lat1)
phi2 = radians(lat2)
delta_phi    = phi2 - phi1
delta_lambda = radians(lon2 - lon1)

h = sin²(delta_phi / 2)
    + cos(phi1) * cos(phi2) * sin²(delta_lambda / 2)

d(a,b) = 2 * R * asin(sqrt(h))
```

where:

```text
R = 6,371,008.8 metres
```

The result is an approximate great-circle distance on a spherical Earth. It is appropriate for the
short Helsinki-scale distances used by the MVP, but it is not a walking distance, travel time, road
distance, or parcel-access distance.

The unit test verifies that a latitude change of `0.001°` near Helsinki is approximately `111.2 m`.

### 2.2 Regular candidate grid

For a bounding box, candidate points are generated using approximate degree steps.

```text
middle_latitude = (south + north) / 2

latitude_step_degrees = spacing_metres / 111,320

longitude_step_degrees =
    spacing_metres
    / (111,320 * max(cos(radians(middle_latitude)), 0.01))
```

The `cos(latitude)` term accounts approximately for longitude lines getting closer together toward
the poles. The `0.01` floor prevents division by zero near a pole.

Current input limits are:

```text
100 m <= grid spacing <= 2,000 m
candidate count <= configured max_candidates (400 by default)
```

This is an approximation, not a projected-coordinate grid. It also does not currently ensure that
a candidate is on a valid commercial parcel rather than water, a road, or restricted land.

### 2.3 Area-query padding

Area analysis fetches one shared Overpass region and pads it so POIs outside the visible bounding
box can still contribute to edge candidates.

Implementation: [`backend/app/integrations/overpass.py`](../backend/app/integrations/overpass.py).

```text
latitude_padding_degrees  = padding_metres / 111,320
longitude_padding_degrees = padding_metres / 55,800
```

The default padding is `1,000 m`. The longitude conversion is a Helsinki-oriented approximation;
it is not latitude-dependent and should not be treated as globally accurate.

### 2.4 PostGIS radius predicate

The persistence boundary defines an indexed database radius query using:

```text
ST_DWithin(candidate_location, query_location, radius_metres)
```

Implementation: [`backend/app/db/spatial.py`](../backend/app/db/spatial.py).

Because candidate locations use PostGIS `Geography(POINT, 4326)`, the distance argument is in
metres. This query builder is not yet part of the live scoring pipeline.

## 3. Raw geographic feature metrics

Implementation: [`backend/app/services/features.py`](../backend/app/services/features.py).

### 3.1 Radius count

Every count feature is an inclusive radial count:

```text
N(category, radius) =
    sum(1 for POI in P
        if POI.category == category
        and d(L, POI.location) <= radius)
```

Implemented count features:

| Feature | Formula | Unit |
| --- | --- | --- |
| `cafes_250m` | `N(cafe, 250)` | POIs |
| `cafes_500m` | `N(cafe, 500)` | POIs |
| `cafes_1000m` | `N(cafe, 1000)` | POIs |
| `restaurants_500m` | `N(restaurant, 500)` | POIs |
| `universities_500m` | `N(university, 500)` | POIs |
| `universities_1000m` | `N(university, 1000)` | POIs |
| `bus_stops_250m` | `N(bus_stop, 250)` | POIs |
| `bus_stops_500m` | `N(bus_stop, 500)` | POIs |
| `stations_1000m` | `N(station, 1000)` | POIs |
| `offices_500m` | `N(office, 500)` | POIs |
| `offices_1000m` | `N(office, 1000)` | POIs |
| `parking_500m` | `N(parking, 500)` | POIs |
| `supermarkets_1000m` | `N(supermarket, 1000)` | POIs |

These are counts of mapped OSM objects, not people, businesses, capacity, floor area, service
frequency, or foot traffic. One large university and one small college each contribute `1`.

### 3.2 Distance to city center

```text
distance_to_center_km = round(d(L, city_center) / 1,000, 3)
```

The current city center is fixed to:

```text
Helsinki center = (60.1699, 24.9384)
```

This metric is therefore meaningful only for the current Helsinki MVP.

### 3.3 POI density within 500 metres

The area of the 500 m circle is calculated in square kilometres:

```text
radius = 0.5 km
area_500 = pi * radius²
         = pi * 0.5²
         ≈ 0.785398 km²
```

All normalized POI categories contribute equally:

```text
pois_within_500 = sum(1 for POI in P if d(L, POI.location) <= 500 m)

poi_density_500m = round(pois_within_500 / area_500, 3)
```

Unit:

```text
mapped POIs per square kilometre
```

This is not population density or commercial floor-area density.

### 3.4 Important radius limitation

The point endpoint permits a requested fetch radius from `250` to `2,000 m`, while the feature
schema always contains features up to `1,000 m`.

If a caller requests only `250 m`, the system cannot observe POIs between `250` and `1,000 m` and
will undercount the larger-radius features. Therefore, under the current implementation:

```text
requested radius < largest feature radius
    => incomplete larger-radius features
```

This is a known correctness limitation, not missing-value evidence.

## 4. Normalization formula

Implementation: [`backend/app/ml/models.py`](../backend/app/ml/models.py).

Raw counts are converted to `0..1` with a linear saturation function:

```text
S(x,T) = clip(x / T, 0, 1)
       = min(max(x / T, 0), 1)
```

Interpretation:

- `x = 0` gives `0`.
- `x = T / 2` gives `0.5`.
- `x >= T` gives `1`.
- Values above `T` are indistinguishable after saturation.

The thresholds `T` are hand-selected heuristic constants. They have not been estimated from outcome
data or calibrated with domain experts.

## 5. Baseline score components

Implementation: [`backend/app/ml/models.py`](../backend/app/ml/models.py).

### 5.1 Competition

```text
competition = 1 - S(cafes_500m, 20)
```

Equivalent piecewise form:

```text
if cafes_500m <= 20: competition = 1 - cafes_500m / 20
if cafes_500m > 20:  competition = 0
```

Higher values are treated as better. The formula assumes every additional café is negative and that
competition becomes maximally unfavorable at 20 cafés. It does not model the possibility that café
clusters signal strong demand.

### 5.2 Transport

```text
transport_input = bus_stops_500m + 3 * stations_1000m
transport = S(transport_input, 15)
```

One mapped station is treated as equivalent to three mapped bus stops. Service frequency, routes,
walking access, and travel time are not included.

### 5.3 Target-audience proxy

```text
audience_input = 4 * universities_1000m + offices_1000m
target_audience = S(audience_input, 25)
```

One mapped university is treated as equivalent to four mapped offices. This component is always
calculated the same way; the request's `target_audience` list is currently not used. The name means
"student/office proxy" in the implementation, not a user-specific audience estimate.

### 5.4 Commercial activity

```text
commercial_input = restaurants_500m + offices_500m
commercial_activity = S(commercial_input, 25)
```

Restaurants and offices contribute equally. Object size, capacity, employment, opening hours, and
business turnover are not represented.

### 5.5 Centrality

```text
centrality = max(0, 1 - distance_to_center_km / 10)
```

This is a linear decay from `1` at Helsinki center to `0` at 10 km or farther. It assumes closer to
the single city center is always better.

### 5.6 Amenities

```text
amenities_input = parking_500m + supermarkets_1000m
amenities = S(amenities_input, 8)
```

Parking and supermarkets contribute equally. Capacity and accessibility are not represented.

## 6. Weighted deterministic baseline

Weights are defined in [`backend/app/configuration.py`](../backend/app/configuration.py).

```text
B = 0.20 * transport
  + 0.25 * target_audience
  + 0.15 * competition
  + 0.15 * commercial_activity
  + 0.10 * centrality
  + 0.15 * amenities
```

The weights sum to:

```text
0.20 + 0.25 + 0.15 + 0.15 + 0.10 + 0.15 = 1.00
```

Because every component is in `[0,1]`, the weighted baseline is also in `[0,1]`. The stored baseline
score is rounded to four decimal places:

```text
base_score = round(B, 4)
```

These weights express design assumptions. They are not learned coefficients and do not measure
causal importance.

## 7. Rule metrics and modifiers

Implementation: [`backend/app/services/rules.py`](../backend/app/services/rules.py).

Each rule returns a Boolean trigger and a fixed modifier. If its condition is false, its modifier is
`0`.

| Rule | Trigger | Modifier |
| --- | --- | ---: |
| University proximity | `universities_1000m >= 2` | `+0.08` |
| Office concentration | `offices_500m >= 10` | `+0.06` |
| Transport access | `bus_stops_500m >= 8 OR stations_1000m >= 1` | `+0.05` |
| Competition saturation | `cafes_500m >= 15` | `-0.12` |
| Low activity | `poi_density_500m < 3` | `-0.08` |

Total rule adjustment:

```text
A = sum(modifier_i for every triggered rule i)
```

With the current rules, the theoretical adjustment range is:

```text
minimum A = -0.12 - 0.08 = -0.20
maximum A =  0.08 + 0.06 + 0.05 = 0.19
```

The exact extremes may not be equally plausible in real data. Rules can also reuse evidence already
present in baseline components, which can double-count universities, offices, transport, cafés, and
general POI activity.

## 8. Final decision formula

Implementation: [`backend/app/services/decision.py`](../backend/app/services/decision.py).

```text
raw_final = B + A
F = clip(raw_final, 0, 1)
final_score = round(F, 4)
```

Clipping means:

- A negative adjustment cannot produce a score below `0`.
- A positive adjustment cannot produce a score above `1`.
- Different raw values can become identical after clipping.

### 8.1 Grade thresholds

```text
if F >= 0.70:               grade = "high"
if 0.40 <= F < 0.70:        grade = "medium"
if F < 0.40:                grade = "low"
```

These thresholds are product labels, not statistically validated risk bands.

### 8.2 Positive and negative factors

```text
positive factors = reasons from triggered rules with modifier > 0
negative factors = reasons from triggered rules with modifier < 0
```

Untriggered rules do not become displayed factors. Component contributions are not currently added
to these explanation lists.

## 9. Current `confidence` metric

Implementation: [`backend/app/ml/models.py`](../backend/app/ml/models.py).

```text
observed = min(1, poi_density_500m / 20)
confidence = round(0.55 + 0.35 * observed, 3)
```

Therefore:

```text
minimum confidence = 0.55
maximum confidence = 0.90
full saturation occurs at 20 POIs/km²
```

This metric is a heuristic based only on mapped POI density. It is not:

- a probability that the score is correct;
- a prediction interval;
- statistical confidence;
- calibration confidence;
- a direct measurement of OSM completeness.

`evidence_coverage` would be a more accurate name until a validated uncertainty method exists.

## 10. Ranking formula

Implementation: [`backend/app/services/analysis.py`](../backend/app/services/analysis.py).

Candidates are sorted by final score in descending order:

```text
ordered_candidates = sort(candidates, key=final_score, descending=True)
result = first K ordered_candidates
```

The API assigns ranks starting at `1` after sorting. There is no explicit tie-breaker, so equal-score
candidates preserve their original grid-generation order because Python sorting is stable.

This is score sorting, not a trained learning-to-rank model.

## 11. Frontend display and visualization formulas

Implementation:

- [`frontend/src/App.tsx`](../frontend/src/App.tsx)
- [`frontend/src/mapData.ts`](../frontend/src/mapData.ts)
- [`frontend/src/MapView.tsx`](../frontend/src/MapView.tsx)

### 11.1 Percentage display

```text
displayed suitability = round(100 * final_score)
displayed component   = round(100 * component)
displayed confidence  = round(100 * confidence)
```

The UI percentage is only a rescaling. For example, `0.8054` is displayed as `81/100`; it does not
mean an 81% probability of success.

### 11.2 Candidate marker radius

MapLibre linearly interpolates candidate circle radius between `7 px` and `12 px`:

```text
marker_radius_px = 7 + 5 * final_score
```

for scores in `[0,1]`.

### 11.3 Heatmap weight

```text
candidate heatmap weight = final_score
POI evidence weight      = 0.4
```

MapLibre then calculates screen-space heatmap density from those weights, the configured radius of
`28 px`, and intensity `1.2`. The final rendered heatmap density is a visualization-engine output,
not a backend business metric.

Currently area analysis returns only top-K candidates, so the displayed heatmap does not represent
the complete evaluated candidate surface.

## 12. Worked scoring example

The existing scoring test constructs the following evidence near the candidate:

```text
bus_stops_500m       = 8
offices_500m         = 10
offices_1000m        = 10
universities_1000m   = 2
supermarkets_1000m   = 1
cafes_500m           = 0
restaurants_500m     = 0
stations_1000m       = 0
parking_500m         = 0
distance_to_center   = 0 km
POIs within 500 m    = 21
```

Feature density:

```text
poi_density_500m = 21 / (pi * 0.5²)
                 ≈ 26.738 POIs/km²
```

Components:

```text
competition        = 1 - S(0, 20)        = 1.0000
transport          = S(8 + 3*0, 15)      = 0.5333
target_audience    = S(4*2 + 10, 25)     = 0.7200
commercial_activity= S(0 + 10, 25)       = 0.4000
centrality         = max(0, 1 - 0/10)     = 1.0000
amenities          = S(0 + 1, 8)         = 0.1250
```

Baseline:

```text
B = 0.20*0.5333
  + 0.25*0.7200
  + 0.15*1.0000
  + 0.15*0.4000
  + 0.10*1.0000
  + 0.15*0.1250
  ≈ 0.6154
```

Triggered rules:

```text
university proximity  +0.08
office concentration  +0.06
transport access      +0.05

A = 0.19
```

Final result:

```text
F = clip(0.6154 + 0.19, 0, 1)
  = 0.8054

grade = high
display = 81/100
```

Evidence confidence:

```text
observed = min(1, 26.738 / 20) = 1
confidence = 0.55 + 0.35*1 = 0.90
```

## 13. Engineering and operational metrics

These metrics are required by the project roadmap. Most are not yet emitted automatically by the
application.

### 13.1 Test coverage

Statement coverage is conceptually:

```text
coverage_percent = 100 * executed_statements / measurable_statements
```

Coverage describes which code statements ran during tests. It does not prove behavioral
correctness, test quality, or production reliability.

### 13.2 Latency percentiles

For `n` observed durations sorted from smallest to largest, percentile `p` is a quantile of that
distribution. Operational reporting should include at least:

```text
p50 = median latency
p95 = latency at or below which approximately 95% of observations fall
```

Required future timings include external provider, feature extraction, model inference, database,
candidate scoring, and total analysis latency. No production percentile telemetry is currently
implemented.

### 13.3 Cache hit rate

```text
cache_hit_rate = cache_hits / (cache_hits + cache_misses)
```

Cache reads exist today, but hit/miss counters are not yet collected.

### 13.4 Successful-analysis rate

```text
successful_analysis_rate = completed_analyses / started_analyses
```

The roadmap proposes this as a service objective. It is not currently measured.

## 14. Planned data-quality metrics

These belong to the ML dataset phases and are not yet calculated by production code.

### 14.1 Missingness rate

For feature `j`:

```text
missing_rate_j = missing_values_j / total_rows
```

Report missingness by source, geography, time period, and target group where relevant. A zero-filled
feature is not necessarily non-missing.

### 14.2 Duplicate rate

```text
duplicate_rate = rows_identified_as_duplicates / total_rows
```

The duplicate definition must be explicit, for example identical business ID, coordinates and
timestamp, or observations within a documented spatial/temporal tolerance.

### 14.3 Class prevalence

For a binary target:

```text
positive_prevalence = positive_examples / all_labeled_examples
```

This is needed to interpret accuracy, precision, recall, PR-AUC, and naive baselines.

## 15. Planned supervised-model metrics

No values for these metrics have been measured in this project yet. The target definition determines
which subset is valid.

### 15.1 Binary classification counts

```text
TP = predicted positive and actually positive
FP = predicted positive but actually negative
TN = predicted negative and actually negative
FN = predicted negative but actually positive
```

### 15.2 Precision

```text
precision = TP / (TP + FP)
```

Question answered: of the locations predicted as positive, how many were actually positive?

Use when false recommendations are expensive. Precision depends on the decision threshold and class
prevalence.

### 15.3 Recall

```text
recall = TP / (TP + FN)
```

Question answered: of all genuinely positive locations, how many did the model find?

Use when missing a good opportunity is expensive.

### 15.4 F1 score

```text
F1 = 2 * precision * recall / (precision + recall)
   = 2*TP / (2*TP + FP + FN)
```

F1 balances precision and recall through their harmonic mean. It ignores true negatives and does
not measure calibration.

### 15.5 ROC-AUC

ROC-AUC is the area under the curve of:

```text
true_positive_rate  = TP / (TP + FN)
false_positive_rate = FP / (FP + TN)
```

across classification thresholds. An equivalent interpretation is the probability that a randomly
selected positive example receives a higher score than a randomly selected negative example,
subject to tie handling.

ROC-AUC can look optimistic for highly imbalanced outcomes and does not evaluate probability
calibration or top-K usefulness.

### 15.6 Precision-recall AUC

PR-AUC summarizes the precision-recall curve across thresholds. It is often more informative than
ROC-AUC for rare positive outcomes. Its baseline depends on positive prevalence, so results across
datasets with different prevalence are not directly comparable without context.

### 15.7 Calibration

For a well-calibrated probabilistic model:

```text
among predictions near probability p,
approximately fraction p should be positive
```

A common summary is Expected Calibration Error:

```text
ECE = sum over bins b of
      (count_b / n) * abs(observed_rate_b - mean_prediction_b)
```

Calibration must be evaluated on held-out data. The current heuristic score must not be interpreted
as a calibrated probability.

## 16. Planned regression metrics

Use these only if the target is continuous, such as revenue or growth.

Given true values `y_i`, predictions `y_hat_i`, and `n` observations:

### 16.1 Mean absolute error

```text
MAE = (1/n) * sum(abs(y_i - y_hat_i))
```

MAE is in the target's original unit and weights errors linearly.

### 16.2 Root mean squared error

```text
RMSE = sqrt((1/n) * sum((y_i - y_hat_i)²))
```

RMSE is also in the target's unit but penalizes large errors more strongly than MAE.

Report both when large failures matter, and map residuals to detect geographic structure hidden by
one aggregate value.

## 17. Planned ranking metrics

Ranking metrics must be calculated within a query group, such as one city-area request, and then
aggregated across groups. They are not currently implemented.

### 17.1 Precision at K

```text
Precision@K = relevant items in the first K results / K
```

This measures top-K usefulness but ignores ordering within the first K and relevant results below K.

### 17.2 Average Precision and MAP

For one ranked query:

```text
AP@K = (1 / min(number_of_relevant_items, K))
       * sum from i=1 to K of Precision@i * relevance_i
```

where `relevance_i` is `1` when the item at rank `i` is relevant and `0` otherwise.

Across `Q` queries:

```text
MAP@K = (1/Q) * sum(AP@K for each query)
```

MAP rewards placing binary-relevant candidates early.

### 17.3 Discounted cumulative gain

For graded relevance:

```text
DCG@K = sum from i=1 to K of (2^relevance_i - 1) / log2(i + 1)
```

The logarithmic denominator discounts relevant items appearing lower in the ranking.

### 17.4 Normalized discounted cumulative gain

```text
NDCG@K = DCG@K / IDCG@K
```

`IDCG@K` is the DCG of the ideal ordering for the same candidates. NDCG normally lies in `[0,1]`
when relevance is non-negative. It supports graded relevance and emphasizes correct ordering near
the top.

### 17.5 Top-K stability

The collaborative roadmap requires checking whether the recommended set changes under folds,
seeds, data refreshes, or approximations. One useful set-overlap measure is Jaccard similarity:

```text
Jaccard(A,B) = size(A intersection B) / size(A union B)
```

where `A` and `B` are two top-K candidate sets. This is a proposed diagnostic, not yet an implemented
project metric.

## 18. Planned explainability identity

For additive explanation methods such as SHAP, local contributions should reconcile with the model
output in the explanation method's output space:

```text
model_output(x) = expected_model_output + sum(feature_contribution_j)
```

For classifiers, that output space may be raw margin/log-odds rather than probability, depending on
the explainer configuration. Contributions must therefore not be shown as probability-point changes
unless that interpretation is mathematically valid.

SHAP is not currently installed or calculated. Rule modifiers are the only implemented local
explanation contributions.

## 19. Interpretation rules

Use these rules whenever presenting project results:

1. Do not call the deterministic score a probability, accuracy, expected revenue, or predicted
   success.
2. Do not call current `confidence` statistical confidence; describe it as a POI-density evidence
   heuristic.
3. Keep raw counts, normalized components, baseline score, rule adjustment, and final score
   separate.
4. Report units and radius with every geographic feature.
5. Report the dataset version, geographic/time split, target, and uncertainty with every future ML
   metric.
6. Compare future models and the deterministic baseline on identical observations and holdouts.
7. Never report random-split performance as proof of geographic generalization.
8. Treat feature importance and SHAP values as model behavior, not causal effects.
9. Include negative results and geographic/subgroup errors, not only aggregate best scores.
10. If labels are not defensible, retain the deterministic system rather than manufacturing ML
    metrics.
