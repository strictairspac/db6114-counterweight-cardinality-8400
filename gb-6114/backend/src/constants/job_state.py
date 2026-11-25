from enum import StrEnum


class JobState(StrEnum):
    QUEUED = "queued"
    DONE = "done"
    FAILED = "failed"


class RevisionState(StrEnum):
    COMPUTING = "computing"
    READY = "ready"
    FAILED = "failed"
