import datetime

from beanhub_forms.data_types.form import FormSchema
from fastapi.encoders import jsonable_encoder
from wtforms import Form as WTForm


def convert_fields_for_js(form: WTForm, form_schema: FormSchema) -> list:
    fields = jsonable_encoder(form_schema.fields, exclude_unset=True)
    for field in fields:
        field_errors = form.errors.get(field["name"])
        if field_errors is not None:
            field["error"] = ", ".join(field_errors)
        field_value = form.data.get(field["name"])
        if field_value is not None:
            if isinstance(field_value, datetime.date):
                field["default"] = field_value.strftime("%Y-%m-%d")
            else:
                field["default"] = field_value
        display_name = field.pop("display_name", None)
        if display_name is not None:
            # Convert to js naming
            field["displayName"] = display_name
    return fields
