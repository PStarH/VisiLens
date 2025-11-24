# VisiLens Feature Roadmap

We're not trying to port every single VisiData feature. Instead, we're focusing on the ones where a web interface can really outshine a terminal UI—specifically around visualization and mouse interaction.

Here's what we're prioritizing to make VisiLens a killer app for data exploration.

## Data Distribution & Analysis

VisiData's engine is great here, but ASCII charts have their limits. We can do better with the DOM.

### Frequency Tables (Histograms)
In VisiData, `Shift+F` creates a new frequency sheet. In VisiLens, we want this to be a sidebar analysis.
- **Goal:** User clicks "Analyze" on a column header, and a sidebar slides out with a bar chart showing the distribution.
- **Why:** It's the fastest way to spot outliers or uneven distributions.

### Column Statistics
Instead of a status bar summary, we can use the mouse hover state.
- **Goal:** Hovering over a column header shows a card with key stats: null rate, unique count, mean/max/min.

## Cleaning & Correction

These are the bread-and-butter features for anyone working with messy CSVs.

### Type Casting
VisiData sometimes guesses types wrong (IDs as numbers, dates as strings).
- **Goal:** Right-click column header -> "Change Type" -> Select Int/Float/Date/String.

### Renaming Columns
- **Goal:** Double-click a column header to rename it inline.

## Filtering & Selection

Making it easier to drill down into data without writing regex.

### Filter by Value
- **Goal:** Right-click a cell -> "Filter by this value" (or "Exclude this value").

### Export Selected Rows
- **Goal:** Checkbox selection for rows, then a button to "Export Selected" to JSON or CSV.

---

## Technical Implementation Notes

For the backend implementation (v0.2), here is how we map these GUI actions to VisiData's Python API.

### Frequency Table
- **GUI:** User requests analysis on `col`.
- **API:** `vs.FrequencyTable(sheet, [col]).reload()`
- **Implementation:** Instead of pushing a new sheet to the UI stack, we serialize `freq_sheet.rows` (count, percent, value) and send it as JSON for the frontend to render a chart.

### Column Statistics
- **GUI:** Hover event on header.
- **API:** `col.getStats()`
- **Note:** This can be expensive. We should use `sheet.executor` to run this off the main thread for large datasets.

### Type Conversion
- **GUI:** User selects new type.
- **API:** Set `col.type` (e.g., `int`, `float`, `date`) and call `sheet.recalc()`.

### Filter by Value
- **GUI:** Filter where `col == value`.
- **API:** `sheet.select(lambda r, c=col, v=val: c.getValue(r) == v)`, then use `sheet.only_selected()` or similar logic to create a view.
