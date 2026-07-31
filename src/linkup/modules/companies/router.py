from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from linkup.api.dependencies import SessionDep
from linkup.modules.auth.dependencies import CurrentUserDep
from linkup.modules.companies.exceptions import (
    CompanyNotFoundError,
    CompanyPermissionDeniedError,
    CompanySlugAlreadyExistsError,
)
from linkup.modules.companies.schemas import (
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
)
from linkup.modules.companies.service import (
    create_company,
    delete_company,
    get_company_by_id,
    list_companies,
    update_company,
)

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_endpoint(
    payload: CompanyCreate,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> CompanyResponse:
    try:
        company = await create_company(
            db,
            current_user.id,
            payload,
        )
    except CompanySlugAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company slug already exists",
        ) from error

    return CompanyResponse.model_validate(company)


@router.get(
    "",
    response_model=list[CompanyResponse],
)
async def list_companies_endpoint(
    current_user: CurrentUserDep,
    db: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CompanyResponse]:
    companies = await list_companies(
        db,
        limit,
        offset,
    )

    return [CompanyResponse.model_validate(company) for company in companies]


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
)
async def get_company_endpoint(
    company_id: UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> CompanyResponse:
    try:
        company = await get_company_by_id(
            db,
            company_id,
        )
    except CompanyNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from error

    return CompanyResponse.model_validate(company)


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
)
async def update_company_endpoint(
    company_id: UUID,
    payload: CompanyUpdate,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> CompanyResponse:
    try:
        company = await update_company(
            db,
            company_id,
            current_user.id,
            payload,
        )
    except CompanyNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from error
    except CompanyPermissionDeniedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the company owner can update it",
        ) from error
    except CompanySlugAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company slug already exists",
        ) from error

    return CompanyResponse.model_validate(company)


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_company_endpoint(
    company_id: UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> None:
    try:
        await delete_company(
            db,
            company_id,
            current_user.id,
        )
    except CompanyNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from error
    except CompanyPermissionDeniedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the company owner can delete it",
        ) from error
