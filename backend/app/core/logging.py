import logging


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
