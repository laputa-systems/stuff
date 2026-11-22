from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import PurePosixPath
from typing import cast

FORK_CI_WORKFLOW_NAMES = frozenset({"ci", "lint", "test"})
FORK_WORKFLOW_NAMES = FORK_CI_WORKFLOW_NAMES | {"android", "prerelease", "release"}


def is_fork_workflow(path: str | PurePosixPath) -> bool:
    workflow_path = str(path).split("@", 1)[0]
    return PurePosixPath(workflow_path).stem.casefold() in FORK_WORKFLOW_NAMES


def workflow_jobs(document: object) -> Iterator[tuple[str, Mapping[str, object]]]:
    if not isinstance(document, Mapping):
        return
    jobs = document.get("jobs")
    if isinstance(jobs, Mapping):
        for name, job in jobs.items():
            if isinstance(name, str) and isinstance(job, Mapping):
                yield name, cast(Mapping[str, object], job)


def job_container_images(job_id: str, job: Mapping[str, object]) -> Iterator[tuple[str, str]]:
    fields = {f"jobs.{job_id}.container": job.get("container")}
    services = job.get("services")
    if isinstance(services, Mapping):
        fields.update({
            f"jobs.{job_id}.services.{name}": value
            for name, value in services.items()
            if isinstance(name, str)
        })
    for location, value in fields.items():
        image = value.get("image") if isinstance(value, Mapping) else value
        if isinstance(image, str):
            yield location, image
