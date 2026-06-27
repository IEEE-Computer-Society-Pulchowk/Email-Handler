from typing import Optional

import pandas as pd


def fetch_sheet_dataframe(
    sheets_service,
    spreadsheet_id: str,
    sheet_name: str,
    range_name: Optional[str] = None,
) -> pd.DataFrame:
    effective_range = range_name or f"{sheet_name}!A:Z"
    sheet = sheets_service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=spreadsheet_id, range=effective_range)
        .execute()
    )
    values = result.get("values", [])

    if not values:
        return pd.DataFrame()

    return pd.DataFrame(values[1:], columns=values[0])
