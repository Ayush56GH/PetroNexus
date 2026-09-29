"""
PetroNexus Table & Structured Section Extractor
Extracts operational data tables from document pages (mud rheology, casing specs, formation tops, events).
"""
import re
from typing import List, Dict, Any

class TableExtractor:

    @staticmethod
    def extract_tables_from_text(page_text: str) -> List[Dict[str, Any]]:
        """
        Detects tabular patterns in extracted page text and returns structured tables with headers and rows.
        """
        lines = [line.strip() for line in page_text.split("\n") if line.strip()]
        tables = []
        current_table = []
        is_in_table = False
        table_title = "Operational Table"

        for line in lines:
            # Check for table header keywords
            if any(k in line.lower() for k in ["formation top", "casing string", "mud properties", "event log", "bha details"]):
                table_title = line
                is_in_table = True
                continue

            # Check if line contains delimiter or multiple tab/spaced columns
            cols = [c.strip() for c in re.split(r"\s{2,}|\t|\|", line) if c.strip()]
            if len(cols) >= 3 and is_in_table:
                current_table.append(cols)
            elif is_in_table and current_table:
                # End of table
                if len(current_table) >= 2:
                    tables.append({
                        "title": table_title,
                        "headers": current_table[0],
                        "rows": current_table[1:]
                    })
                current_table = []
                is_in_table = False

        if is_in_table and len(current_table) >= 2:
            tables.append({
                "title": table_title,
                "headers": current_table[0],
                "rows": current_table[1:]
            })

        return tables
