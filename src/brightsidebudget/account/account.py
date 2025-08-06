from pydantic import BaseModel, Field, model_validator
import polars as pl

from brightsidebudget.account.account_type import AccountType

class Account(BaseModel):
    model_config = {"frozen": True}

    name: str = Field(..., min_length=1, description="Name of the account")
    type: AccountType = Field(..., description="Type of the account")
    group: str = Field(default="", description="Group of the account")
    subgroup: str = Field(default="", description="Sub-group of the account")
    number: int = Field(..., ge=1000, le=6999, description="Account number")


    @model_validator(mode='before')
    def validate_account(cls, data: dict) -> dict:
        """
        Transform the 'type' field to an AccountType instance if it is a string.
        """
        if isinstance(data.get('type'), str):
            data['type'] = AccountType(name=data['type'])
        return data

    @model_validator(mode='after')
    def validate_number(self):
        """
        Validate the account number based on its type.
        """
        self.type.validate_number(self.number)
        return self

    def sort_key(self) -> int:
        """
        Returns a sort key for the account based on its number.
        """
        return self.number

    @staticmethod
    def to_dataframe(accounts: list['Account']) -> pl.DataFrame:
        """
        Convert a list of Account objects to a dictionary suitable for DataFrame creation.
        """
        xs = [a.model_dump(warnings=False) for a in accounts]
        for x in xs:
            x['type'] = x['type']["name"]
        df = pl.DataFrame(
            xs,
            schema={
                'name': pl.String,
                'type': pl.String,
                'group': pl.String,
                'subgroup': pl.String,
                'number': pl.Int64
            }
        ).rename(
            {
                'name': 'Compte',
                'type': 'Type',
                'group': 'Groupe',
                'subgroup': 'Sous-groupe',
                'number': 'Numéro'
            }
        )
        return df

    @staticmethod
    def from_dataframe(df: pl.DataFrame) -> list['Account']:
        """
        Convert a DataFrame to a list of Account objects.
        """
        accounts = []
        for row in df.to_dicts():
            acc = Account(
                name=row['Compte'],
                type=AccountType(name=row['Type']),
                group=row["Groupe"] if row["Groupe"] else "",
                subgroup=row["Sous-groupe"] if row["Sous-groupe"] else "",
                number=row['Numéro']
            )
            accounts.append(acc)
        return accounts