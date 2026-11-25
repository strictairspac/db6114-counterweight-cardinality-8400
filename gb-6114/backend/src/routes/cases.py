from fastapi import APIRouter, Depends

from src.config.resources import engine
from src.controllers.access import identity, operator
from src.controllers.workbench import new_case, new_correction, new_run
from src.schemas.cases import CaseCorrection, CaseDetail, CaseInput, CaseSummary, RevisionEntry
from src.schemas.runs import RunEntry, RunInput
from src.services import cases

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("", response_model=list[CaseSummary], dependencies=[Depends(identity)])
def list_cases():
    with engine.connect() as db:
        return cases.list_entries(db)


@router.get("/{case_id}", response_model=CaseDetail, dependencies=[Depends(identity)])
def case_detail(case_id: int):
    with engine.connect() as db:
        return cases.detail(db, case_id)


@router.get("/{case_id}/revisions", response_model=list[RevisionEntry], dependencies=[Depends(identity)])
def case_revisions(case_id: int):
    with engine.connect() as db:
        return cases.history(db, case_id)


@router.post("", response_model=CaseDetail, status_code=201)
def register(form: CaseInput, user=Depends(operator)):
    return new_case(form, user)


@router.put("/{case_id}", response_model=RevisionEntry, status_code=202)
def correct(case_id: int, form: CaseCorrection, user=Depends(operator)):
    return new_correction(case_id, form, user)


@router.post("/{case_id}/runs", response_model=RunEntry, status_code=202)
def schedule(case_id: int, form: RunInput, user=Depends(operator)):
    return new_run(case_id, form, user)
