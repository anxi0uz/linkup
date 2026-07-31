from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from linkup.models import Company
from linkup.modules.companies.exceptions import (
    CompanyNotFoundError,
    CompanyPermissionDeniedError,
    CompanySlugAlreadyExistsError,
)
from linkup.modules.companies.schemas import CompanyCreate, CompanyUpdate

log = structlog.get_logger(
    component="companies.service",
)


async def create_company(
    db: AsyncSession,
    owner_id: UUID,
    data: CompanyCreate,
) -> Company:
    company = Company(
        **data.model_dump(),
        owner_id=owner_id,
    )

    db.add(company)

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise CompanySlugAlreadyExistsError from error

    await db.refresh(company)

    log.info(
        "company_created",
        company_id=str(company.id),
        owner_id=str(owner_id),
    )

    return company


async def list_companies(
    db: AsyncSession,
    limit: int,
    offset: int,
) -> list[Company]:
    companies = await db.scalars(
        select(Company)
        .order_by(
            Company.created_at.desc(),
            Company.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return list(companies.all())


async def get_company_by_id(
    db: AsyncSession,
    company_id: UUID,
) -> Company:
    company = await db.get(Company, company_id)

    if company is None:
        raise CompanyNotFoundError

    return company


def ensure_company_owner(
    company: Company,
    owner_id: UUID,
) -> None:
    if company.owner_id != owner_id:
        raise CompanyPermissionDeniedError


async def update_company(
    db: AsyncSession,
    company_id: UUID,
    owner_id: UUID,
    data: CompanyUpdate,
) -> Company:
    company = await get_company_by_id(
        db,
        company_id,
    )
    ensure_company_owner(
        company,
        owner_id,
    )

    updates = data.model_dump(
        exclude_unset=True,
    )

    if not updates:
        return company

    for field, value in updates.items():
        setattr(
            company,
            field,
            value,
        )

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise CompanySlugAlreadyExistsError from error

    await db.refresh(company)

    log.info(
        "company_updated",
        company_id=str(company.id),
        changed_fields=sorted(updates),
    )

    return company


async def delete_company(
    db: AsyncSession,
    company_id: UUID,
    owner_id: UUID,
) -> None:
    company = await get_company_by_id(
        db,
        company_id,
    )
    ensure_company_owner(
        company,
        owner_id,
    )

    await db.delete(company)
    await db.commit()

    log.info(
        "company_deleted",
        company_id=str(company_id),
    )
