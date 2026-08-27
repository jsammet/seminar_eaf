"""A tiny read-only .xlsx reader built on the standard library.

The OASIS demographic tables are distributed as Excel workbooks. Rather than add
``openpyxl`` to the base environment for two small files, we read the sheet
directly: an .xlsx file is a zip archive of XML, and a single worksheet with no
formulas is straightforward to parse.
"""
import re
import xml.etree.ElementTree as ET
import zipfile

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _column_index(reference):
    letters = re.match(r"[A-Z]+", reference).group(0)
    index = 0
    for character in letters:
        index = index * 26 + (ord(character) - 64)
    return index - 1


def read_sheet(path, sheet="sheet1"):
    """Return the worksheet as a list of rows, each a list of strings or None."""
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{NS}si"):
                shared.append("".join(node.text or "" for node in item.iter(f"{NS}t")))

        name = f"xl/worksheets/{sheet}.xml"
        if name not in archive.namelist():
            name = sorted(n for n in archive.namelist() if n.startswith("xl/worksheets/"))[0]
        root = ET.fromstring(archive.read(name))

        sparse_rows = []
        width = 0
        for row in root.iter(f"{NS}row"):
            cells = {}
            for cell in row.findall(f"{NS}c"):
                index = _column_index(cell.get("r"))
                kind = cell.get("t")
                value_node = cell.find(f"{NS}v")
                if kind == "inlineStr":
                    value = "".join(node.text or "" for node in cell.iter(f"{NS}t"))
                elif value_node is None:
                    value = None
                elif kind == "s":
                    value = shared[int(value_node.text)]
                else:
                    value = value_node.text
                cells[index] = value
                width = max(width, index + 1)
            sparse_rows.append(cells)

    table = []
    for cells in sparse_rows:
        line = [None] * width
        for index, value in cells.items():
            line[index] = value
        table.append(line)
    return table


def read_records(path, sheet="sheet1"):
    """Return (fieldnames, list-of-dicts) using the first row as the header."""
    table = read_sheet(path, sheet)
    header = [str(value).strip() if value is not None else f"col_{i}" for i, value in enumerate(table[0])]
    records = []
    for line in table[1:]:
        if all(value in (None, "") for value in line):
            continue
        records.append(dict(zip(header, line)))
    return header, records
