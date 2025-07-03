from pydantic import BaseModel, ConfigDict, Field, model_validator
from brightsidebudget.account.account_type import AccountType


class Account(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Name of the account")
    type: AccountType = Field(..., description="Type of the account")
    group: str = Field(default="", description="Group of the account")
    subgroup: str = Field(default="", description="Sub-group of the account")
    number: int = Field(..., ge=1000, le=6999, description="Account number")


    @model_validator(mode='before')
    def validate_type(cls, data: dict) -> dict:
        """
        Validate the account type.
        """
        if isinstance(data.get('type'), str):
            data['type'] = AccountType(name=data['type'])
        return data

    @model_validator(mode='after')
    def validate_number(self):
        """
        Validate the account number based on its type.
        Raises ValueError if the number is not valid for the account type.
        """
        self.type.validate_number(self.number)
        return self

    def sort_key(self) -> int:
        """
        Returns a sort key for the account based on its number.
        """
        return self.number

    def to_dict(self) -> dict[str, str]:
        return {"Compte": self.name, "Type": self.type.name, "Groupe": self.group,
                "Sous-groupe": self.subgroup, "Numéro": str(self.number)}

    @classmethod
    def from_dict(cls, row: dict[str, str]) -> 'Account':
        return cls(name=row["Compte"], type=AccountType(name=row["Type"]), # type: ignore
                   group=row["Groupe"], subgroup=row["Sous-groupe"],
                   number=int(row["Numéro"]))
