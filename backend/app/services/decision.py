from app.domain.models import LocationFeatures, LocationScore, ModelPrediction, RuleResult


class DecisionEngine:
    def decide(
        self,
        features: LocationFeatures,
        prediction: ModelPrediction,
        rules: list[RuleResult],
    ) -> LocationScore:
        adjustment = sum(rule.modifier for rule in rules if rule.triggered)
        score = min(max(prediction.score + adjustment, 0.0), 1.0)
        triggered = [rule for rule in rules if rule.triggered]
        positives = [rule.reason for rule in triggered if rule.modifier > 0]
        negatives = [rule.reason for rule in triggered if rule.modifier < 0]
        return LocationScore(
            score=round(score, 4),
            grade="high" if score >= 0.7 else "medium" if score >= 0.4 else "low",
            base_score=prediction.score,
            rule_adjustment=round(adjustment, 4),
            confidence=prediction.confidence,
            components=prediction.components,
            features=features,
            rules=rules,
            positive_factors=positives,
            negative_factors=negatives,
        )
