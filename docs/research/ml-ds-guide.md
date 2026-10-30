# ML/DS-гайд: универсальная оценка территории и LLM-слой

## 1. Новая цель

Цель — построить не «модель для кофеен», а универсальную платформу пространственной аналитики:

```text
источники пространственных данных
        ↓
универсальный spatial feature store
        ↓
профиль конкретного бизнеса
        ↓
GIS + правила + MCDA/ML
        ↓
сценарии, ranking и uncertainty
        ↓
LLM объясняет рассчитанные доказательства
```

Система должна хранить факты о территории отдельно от их бизнес-интерпретации. Например, количество
жителей 20–29 лет — факт. Решение о том, положителен ли этот фактор для аптеки, спортзала или
коворкинга, принадлежит бизнес-профилю или валидированной модели.

## 2. Главные принципы

1. Нет универсального score, одинаково правильного для всех бизнесов.
2. Сначала измеряем территорию, затем применяем бизнес-контекст.
3. Каждый признак имеет единицу, географию, дату, источник, лицензию и missing-value policy.
4. Радиус по прямой и пешеходная доступность — разные признаки.
5. LLM работает со схемой и доказательствами, а не придумывает числа.
6. Unsupervised learning описывает структуру данных, но не доказывает коммерческий успех.
7. Supervised ML начинается только после появления честной целевой переменной.
8. Любой score возвращается вместе с компонентами и evidence coverage.

## 3. Пространственная единица анализа

Для первой версии рекомендуется единая сетка `250 × 250 м` в Helsinki metropolitan area, потому
что часть открытых данных HSY уже публикуется на такой сетке. Для каждой ячейки хранятся:

```text
cell_id
geometry
centroid
city
district
observation_date
feature_schema_version
source_versions
```

Точка пользователя связывается с ячейкой, но часть признаков считается для catchment-зон:

- радиусы `250/500/1000 м` для сравнимости с текущим MVP;
- пешеходные изохроны `5/10/15 минут` для реальной доступности;
- административный район только для контекста, а не как единственная единица измерения.

Сетка не должна автоматически считаться местом для аренды. Отдельный eligibility-слой исключает
воду, дороги, промышленные/запрещённые зоны и другие непригодные поверхности.

## 4. Какие группы признаков собрать

### 4.1 Постоянное население

Базовые признаки:

```text
population_total
population_density_km2
population_0_17_share
population_18_29_share
population_30_49_share
population_50_64_share
population_65_plus_share
population_growth_1y
population_growth_5y
```

Плотность:

```text
population_density_km2 = population / inhabited_land_area_km2
```

Если исходная статистическая ячейка пересекает catchment частично:

```text
allocated_population =
    source_population * intersection_area / source_cell_area
```

Это допущение о равномерном распределении населения внутри исходной ячейки. Его нужно записывать в
метаданные. Когда доступны здания и адресное население, можно исследовать более точное распределение.

### 4.2 Catchment population

Население в зоне доступности:

```text
catchment_population =
    sum(population_g * overlap_fraction_g for every intersecting grid g)
```

Полезно считать отдельно:

```text
population_500m
population_1000m
population_walk_10min
target_age_population_walk_10min
```

### 4.3 Дневное население и занятость

Признаки:

```text
jobs_total
jobs_density_km2
establishments_total
employees_by_industry
students_nearby
public_service_capacity
resident_to_job_ratio
```

Не складывай жителей и рабочие места в один `daytime_population` без проверки: один человек может
попасть в разные источники, а рабочее место не равно одновременно присутствующему человеку.
Безопаснее хранить компоненты отдельно и исследовать их веса.

### 4.4 Транспортная доступность

Простого количества остановок недостаточно. Добавь:

```text
stops_walk_5min
stops_walk_10min
departures_weekday_07_10
departures_weekday_16_19
departures_weekend
unique_routes
transfer_nodes
travel_time_to_center
travel_time_to_key_destinations
```

Взвешенная доступность возможностей:

```text
accessibility_i = sum(opportunity_j * exp(-beta * travel_time_ij))
```

`beta` задаёт скорость уменьшения ценности с временем поездки. Его нельзя выбирать скрыто: сравни
несколько значений и проведи sensitivity analysis.

### 4.5 Пешеходность и уличная сеть

Возможные признаки:

```text
intersection_density
walkable_road_length_km
average_block_size
sidewalk_or_footway_density
crossing_density
network_centrality
pedestrian_count_mean
pedestrian_count_peak
```

Пешеходные счётчики покрывают только отдельные точки. Не интерполируй их на весь город без проверки
ошибки и uncertainty. Сначала используй их как локальную валидацию proxy-признаков доступности.

### 4.6 Конкуренция

Количество конкурентов в радиусе:

```text
competitors_r = count(competitor within radius r)
```

Distance-decay pressure:

```text
competition_pressure = sum(exp(-distance_j / tau) for each competitor j)
```

где `tau` — масштаб затухания в метрах или минутах ходьбы.

Считать конкуренцию только отрицательной нельзя: кластер конкурентов может указывать на устойчивый
спрос. Поэтому храни отдельно:

```text
competitor_pressure
category_cluster_strength
local_demand_proxies
```

и проверяй их взаимодействие в данных.

### 4.7 Комплементарность и mixed use

Комплементарные объекты зависят от бизнеса. Например, для кафе это офисы, университеты и станции;
для аптеки — клиники, пожилое население и жилые зоны.

Разнообразие категорий можно описать нормированной энтропией Шеннона:

```text
p_k = objects_in_category_k / all_objects
H = -sum(p_k * ln(p_k))
mixed_use_diversity = H / ln(number_of_nonempty_categories)
```

Значение близко к `0`, когда доминирует одна категория, и к `1`, когда категории распределены
равномерно. Метрика зависит от выбранной классификации POI.

### 4.8 Застроенная среда и коммерческая ёмкость

Признаки:

```text
building_coverage_ratio
floor_area_ratio
commercial_floor_area
retail_floor_area
ground_floor_proxy
building_age
vacant_or_developable_area
parking_capacity
distance_to_commercial_building
```

Формулы:

```text
building_coverage_ratio = building_footprint_area / land_area
floor_area_ratio = total_floor_area / land_area
commercial_share = commercial_floor_area / total_floor_area
```

### 4.9 Стоимость и экономическое давление

Если найден законный и воспроизводимый источник:

```text
commercial_rent_m2
residential_rent_proxy
property_price_proxy
income_median
household_disposable_income
rent_to_demand_ratio
```

Не подменяй коммерческую аренду стоимостью жилья без явного названия proxy и проверки корреляции.

### 4.10 Временные признаки

```text
weekday_activity
weekend_activity
morning_peak
evening_peak
seasonality
event_frequency
tourism_season_proxy
```

Храни дату и период агрегации. Среднегодовое значение может скрыть ситуацию, когда район активен
только летом или только в рабочее время.

### 4.11 Среда и риски

В зависимости от бизнеса:

```text
noise_level
air_quality
flood_risk
green_space_access
waterfront_access
construction_disruption
crime_or_safety_proxy, только при законном и корректном источнике
```

Эти признаки могут быть положительными для одного бизнеса и отрицательными для другого.

### 4.12 Качество доказательств

Для каждого признака храни:

```text
source
reference_date
retrieved_at
spatial_resolution
coverage_ratio
missing_reason
imputation_method
license
```

Общий `evidence_coverage` не должен быть простой плотностью POI. Возможный прозрачный вариант:

```text
evidence_coverage =
    sum(required_feature_weight * availability_indicator)
    / sum(required_feature_weight)
```

Дополнительно возвращай возраст данных и список отсутствующих критических признаков.

## 5. Проверенные стартовые источники для Helsinki/Finland

Статус источников нужно повторно проверять перед интеграцией. Дата первичной проверки:
`2026-09-30`.

| Группа | Источник | Что можно получить | Ограничения |
| --- | --- | --- | --- |
| Население | Statistics Finland Population Grid | Численность по сетке 1 км, возрастные группы, временной ряд | 1 км может быть грубо для локального бизнеса |
| Население | HSY/HRI Population Grid | Население и возраст по сетке Helsinki region, последние данные до 250 м | Privacy suppression; специальные значения нельзя считать нулями |
| Доход/занятость | Statistics Finland Paavo | Население, доход, образование, рабочие места по postal code | Грубее сетки, возможен ecological fallacy |
| Детальная статистика | Statistics Finland Grid Database | 250 м: возраст, доход, домохозяйства, занятость, здания | Платный продукт и ограничения распространения; не брать как default |
| Рабочие места | HSY/HRI Enterprise and Establishment Grid | Рабочие места, предприятия, отрасли, 250 м | Задержка около двух лет; нет public-sector jobs; privacy value `-1` |
| Транспорт | Digitransit GTFS/Routing API | Остановки, маршруты, расписания, travel time | Нужны ключ/условия API и кеширование |
| Пешеходы/транспорт | Helsinki traffic measurement API | Счётчики пешеходов, велосипедов и машин | Пространственно неравномерное покрытие |
| Здания | Helsinki WFS buildings | Геометрия, площадь, этажность, назначение | Проверять актуальность атрибутов и CRS |
| Землепользование | SYKE open spatial data / CORINE | Land cover и экологический контекст | Разрешение может быть недостаточным для конкретного помещения |
| POI/сеть | OpenStreetMap | POI, дороги, footways, land use | Неполнота и неодинаковое качество по районам |

Официальные страницы:

- Statistics Finland population grid: <https://stat.fi/en/services/statistical-data-services/geographic-data/population-grid-data-1-km>
- Statistics Finland open data: <https://stat.fi/en/services/statistical-data-services/open-data-and-interfaces>
- Statistics Finland Paavo: <https://stat.fi/en/services/statistical-data-services/statistical-databases/paavo>
- HSY/HRI population grid: <https://hri.fi/data/en/dataset/vaestotietoruudukko>
- HSY/HRI enterprises and establishments: <https://hri.fi/data/en/dataset/helsingin-seudun-tyopaikkaruudukko>
- Digitransit developer portal: <https://portal-dev-api.digitransit.fi/>
- Helsinki buildings: <https://hri.fi/data/en/dataset/helsingin-rakennukset>
- Helsinki traffic measurements: <https://hri.fi/data/dataset/helsingin-liikennemittausten-tilastorajapinta>
- SYKE spatial datasets: <https://www.syke.fi/en/environmental-data/downloadable-spatial-datasets>

## 6. Новый учебный маршрут ML/DS

### Фаза A — Data-source research

Твоя работа:

- создать `source-register.md`;
- сравнить пространственное разрешение, годы, лицензию и missing-value semantics;
- выбрать бесплатный минимальный набор источников;
- определить единую систему координат и дату среза;
- описать, какие источники нельзя публиковать вместе с проектом.

Результат: таблица источников с решением `use / experiment / reject`.

### Фаза B — Spatial data engineering и quality audit

AI-агент реализует загрузку, PostGIS-схемы, reprojection, spatial joins и тесты. Ты:

- исследуешь распределения и специальные privacy-коды;
- проверяешь пропуски, дубликаты и неверные координаты;
- сравниваешь area-weighted и centroid join;
- визуально проверяешь случайную стратифицированную выборку ячеек;
- измеряешь coverage по районам и источникам.

Результат: `dataset-card.md`, EDA notebook и quality report.

### Фаза C — Universal feature store v1

Начни с небольшого набора:

```text
population_density_km2
population_18_29_share
population_65_plus_share
jobs_density_km2
establishments_density_km2
transit_departures_peak
travel_time_to_center
walkable_road_density
commercial_floor_area
poi_diversity
competitor_pressure_by_category
evidence_coverage
```

Твоя работа:

- определить формулу, единицу и направление каждого признака;
- сравнить радиусы с изохронами;
- исследовать skew и transformations (`log1p`, density, percentile rank);
- проверить корреляции и стабильность по времени;
- написать feature dictionary.

Результат: версионированный `feature_schema_v1`.

### Фаза D — Типология районов: первый настоящий DS-проект

До outcome labels сделай unsupervised-анализ:

1. Удали идентификаторы, координаты и признаки утечки района из обучающей матрицы.
2. Обработай пропуски с отдельными indicators.
3. Преобразуй сильно скошенные count/density признаки.
4. Масштабируй признаки.
5. Исследуй PCA для структуры и мультиколлинеарности.
6. Сравни K-Means, Gaussian Mixture и HDBSCAN, если размер данных оправдывает их.
7. Проверь silhouette score, размер кластеров и устойчивость при bootstrap/смене года.
8. Нанеси кластеры на карту и интерпретируй их только по исходным признакам.

Возможные типы:

```text
residential family areas
student/young-adult zones
office-dominated daytime zones
mixed-use high-footfall centers
low-density car-oriented areas
```

Не называй кластер «хорошим для бизнеса». Кластер — описательный тип территории.

Результат: `neighborhood-typology-v1.md` и воспроизводимый notebook.

### Фаза E — Бизнес-профили и multi-criteria analysis

Выбери 2–3 контрастных профиля, например кафе, аптека и спортзал. Для каждого:

- определи аудиторию;
- выбери признаки из общего feature store;
- раздели hard constraints и soft preferences;
- задай направление полезности признаков;
- исследуй насыщение и нелинейность;
- получи веса через прозрачную экспертную процедуру, например pairwise comparison;
- проведи sensitivity analysis весов и top-K стабильности.

Финальный MCDA score:

```text
score_b(cell) =
    clip(sum(weight_bk * utility_bk(feature_k)) + rule_adjustments, 0, 1)
```

Это экспертная decision model, не обученный ML. Результат должен показывать компоненты и сценарии,
например `conservative`, `growth`, `low-cost`.

### Фаза F — Proxy ML, только с честной формулировкой

Если реальных outcome labels нет, можно исследовать proxy-задачи:

- предсказание плотности определённой категории бизнеса;
- вероятность присутствия категории в ячейке;
- восстановление pedestrian counts по доступности и городской форме;
- прогноз изменения коммерческой активности между годами.

Эти модели отвечают на вопросы о городской структуре, но не о прибыльности нового бизнеса.

Используй spatial/temporal holdout, сравни с простыми baseline и исследуй residual maps. Не включай
целевую категорию или её прямой производный признак в `X`, если это превращает задачу в тавтологию.

### Фаза G — Supervised business outcome, когда появятся labels

Только после появления продаж, посещаемости, survival или другого outcome:

- зафиксируй target и prediction horizon;
- считай признаки на момент прогноза;
- сделай geographic/temporal split;
- сравни Dummy, текущий MCDA, linear/logistic и tree models;
- оцени calibration, geographic errors и top-K ranking;
- сохрани model card и frozen holdout.

### Фаза H — LLM analyst

LLM получает не сырые таблицы, а контролируемые инструменты:

```text
parse_business_requirements
list_available_metrics
get_area_evidence
compare_candidates
run_saved_scenario
explain_score
report_missing_evidence
```

Пример структурированного запроса после LLM:

```json
{
  "business_type": "gym",
  "target_audiences": ["young_adults", "office_workers"],
  "hard_constraints": {
    "min_floor_area_m2": 500,
    "max_walk_to_transit_min": 10
  },
  "scenario": "growth",
  "area": {"city": "Helsinki"}
}
```

Pydantic валидирует запрос. Decision Engine выполняет числа. LLM получает результат с источниками и
формулирует сравнение:

```text
факт → метрика → влияние профиля → uncertainty → вывод
```

Обязательные evals LLM-слоя:

- не придумывает отсутствующие значения;
- не меняет рассчитанный score;
- корректно сообщает missing evidence;
- выбирает только существующие metric IDs;
- сохраняет единицы и даты;
- не превращает корреляцию в причинность;
- воспроизводимо объясняет один и тот же structured result.

## 7. Что делать прямо сейчас

### Твои задачи ML/DS/research

1. Заполни поля `[ТВОЁ РЕШЕНИЕ]` в `problem-statement.md`.
2. Создай `source-register.md` и исследуй первые пять источников из таблицы.
3. Выбери сетку и дату первого согласованного среза.
4. Выбери 12–20 признаков feature store v1, не зависящих от типа бизнеса.
5. Для каждого запиши формулу, единицу, источник, resolution, freshness и missing policy.
6. Выбери два контрастных бизнес-профиля для проверки универсальности.
7. Сформулируй три гипотезы, которые можно опровергнуть данными.

### Задачи AI-агента после твоих решений

1. Создать схемы источников, ingestion interfaces и PostGIS-модели.
2. Реализовать воспроизводимую загрузку разрешённых данных.
3. Реализовать reprojection, сетку, spatial joins и feature computation.
4. Добавить lineage, версии, quality checks и тесты.
5. Подготовить notebook templates, не выполняя за тебя анализ и выводы.
6. Интегрировать принятые признаки, профили и модели в API/UI.
7. Создать безопасные LLM tools и evals после стабилизации evidence layer.

## 8. Definition of Done для первого нового этапа

Этап завершён, когда:

- выбрана и обоснована пространственная единица;
- пять источников прошли проверку лицензии и качества;
- построен versioned feature table хотя бы для Helsinki;
- у каждого признака есть формула и provenance;
- privacy-коды не интерпретируются как нули;
- есть карты coverage и missingness;
- выполнена типология районов и проверена её устойчивость;
- два бизнес-профиля используют один feature store;
- LLM ещё не участвует в численном расчёте;
- все ограничения и неподтверждённые гипотезы задокументированы.
