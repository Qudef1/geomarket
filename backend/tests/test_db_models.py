from app.db.models import Candidate


def test_candidate_has_one_explicit_spatial_index() -> None:
    indexes = Candidate.__table__.indexes
    assert {index.name for index in indexes} == {"ix_candidates_location"}
    index = next(iter(indexes))
    assert index.dialect_options["postgresql"]["using"] == "gist"
    assert Candidate.__table__.c.location.type.spatial_index is False
