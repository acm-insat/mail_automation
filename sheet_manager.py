from typing import Tuple, List


class SheetManager:
    """Handles reading and writing to Google Sheets."""

    def __init__(self, service, spreadsheet_id: str):
        self.service = service
        self.spreadsheet_id = spreadsheet_id

    def _col_idx_to_letter(self, n: int) -> str:
        """Converts 0 -> A, 25 -> Z, 26 -> AA, etc."""
        string = ""
        while n >= 0:
            string = chr((n % 26) + 65) + string
            n = (n // 26) - 1
        return string

    def load_data(self, tab_name: str) -> Tuple[List[str], List[List[str]]]:
        """Returns normalized headers and data rows."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{tab_name}!A:Z"
        ).execute()

        values = result.get("values", [])
        if not values:
            return [], []

        headers = [h.strip().replace(" ", "").lower() for h in values[0]]
        return headers, values[1:]

    def update_cell(self, tab_name: str, row_idx: int, col_idx: int, value: str):
        """Updates a specific cell. row_idx is 0-based index from python list."""
        # Convert 0-based row index to Sheets 1-based index
        sheet_row = row_idx + 2 # +1 for 0-index, +1 for header row
        col_letter = self._col_idx_to_letter(col_idx)

        range_name = f"{tab_name}!{col_letter}{sheet_row}"

        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": [[value]]}
        ).execute()