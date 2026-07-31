class CompanyNotFoundError(Exception):
    pass


class CompanySlugAlreadyExistsError(Exception):
    pass


class CompanyPermissionDeniedError(Exception):
    pass
