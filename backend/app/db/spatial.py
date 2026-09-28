from sqlalchemy import Select, select
from sqlalchemy.sql.functions import GenericFunction

from app.db.models import Candidate


class ST_DWithin(GenericFunction[bool]):
    name = "ST_DWithin"
    inherit_cache = True


def candidates_within(location_wkt: str, radius_m: float) -> Select[Candidate]:
    """Build a PostGIS geography radius query; calculation remains in the database."""
    return select(Candidate).where(
        ST_DWithin(Candidate.location, f"SRID=4326;{location_wkt}", radius_m)
    )
