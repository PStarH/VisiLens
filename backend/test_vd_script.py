import visidata
from pathlib import Path
import traceback


def test_vd_loading():
    print(f"VisiData version: {visidata.__version__}")

    # Create a dummy csv
    p = Path("test_vd.csv")
    p.write_text("name,age\nAlice,30\nBob,25")

    vd = visidata.vd

    path = visidata.Path(str(p))
    sheet = vd.openSource(path)

    # Force load
    if hasattr(sheet, "iterload"):
        sheet.rows = list(sheet.iterload())

    if not sheet.columns and sheet.rows:
        first_row = sheet.rows[0]

        try:
            for i, col_name in enumerate(first_row):
                sheet.addColumn(visidata.ColumnItem(str(col_name), i))

            sheet.rows = sheet.rows[1:]

            # Test getting value
            row = sheet.rows[0]
            col = sheet.columns[0]
            print(f"Row: {row}")
            print(f"Col Name: {col.name}")
            print(f"Value: {col.getTypedValue(row)}")

        except Exception:
            traceback.print_exc()

    p.unlink()


if __name__ == "__main__":
    test_vd_loading()
