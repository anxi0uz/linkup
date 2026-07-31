from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RegisteredUser:
    id: str
    email: str
    access_token: str

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
        }


class RegisterUser(Protocol):
    async def __call__(
        self,
        email: str,
        password: str = "test-password",
        first_name: str = "Test",
        last_name: str = "User",
    ) -> RegisteredUser: ...
