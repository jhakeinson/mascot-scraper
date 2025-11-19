from pydantic import BaseModel

class Field(BaseModel):
    category_name: str
    form_label: str
    field_label: str
    field_type: str
    field_values: str  # vertical bar `|` separated string
