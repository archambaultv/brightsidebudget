from typing import Literal
from pydantic import BaseModel, ConfigDict


# Define validation ranges for each account type
VALIDATION_RANGE: dict[str, tuple[int, int]] = {
    "Actifs": (1000, 1999),
    "Passifs": (2000, 2999), 
    "Capitaux propres": (3000, 3999),
    "Revenus": (4000, 4999),
    "Dépenses": (5000, 5999),
    "Non classé": (6000, 6999)
}

class AccountType(BaseModel):
    """
    Represents the type of an account.
    """
    
    name : Literal["Actifs", "Passifs", "Capitaux propres", "Revenus", "Dépenses", "Non classé"]

    def sort_key(self) -> int:
        """
        Returns a sort key for the account type based on its position in the validation range.
        """
        keys = list(VALIDATION_RANGE.keys())
        return keys.index(self.name)

    def validate_number(self, number: int) -> None:
        """
        Validates the account number based on its type.
        Raises ValueError if the number is not valid for the account type.
        """
        min_range, max_range = VALIDATION_RANGE[self.name]
        if not (min_range <= number <= max_range):
            raise ValueError(
                f"Account number {number} is not valid for {self.name} type. "
                f"Expected range: {min_range}-{max_range}"
            )
