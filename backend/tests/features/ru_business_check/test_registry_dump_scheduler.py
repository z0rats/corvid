"""registry_dump_scheduler_service: the thin ru_business_check wrapper around the generic
engine in app.core.registry_dumps.scheduler (tested generically in
tests/core/test_registry_dumps_scheduler.py) names exactly this feature's three dumps."""

from app.features.ru_business_check.service import registry_dump_scheduler_service as svc


def test_every_dump_service_has_a_job():
    from app.features.ru_business_check.config.ru_business_check_config import AVAILABLE_SOURCES

    jobs = svc.dump_jobs()
    sources = {job.source for job in jobs}
    assert sources == {"disqualified", "cbr_warning", "ofac_sdn"}
    assert {"disqualified_dump", "cbr_warning", "ofac_sdn"} <= set(AVAILABLE_SOURCES)
    assert all(job.prefix == "ru_business_check" for job in jobs)
