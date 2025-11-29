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

## Advanced Data Cleaning

Going beyond basic type casting and renaming to full dataset hygiene.

### Fill Null Values
- **Goal:** Right-click a column -> "Fill Nulls" -> Options: "With 0", "With Previous Value", "With Mean/Mode", or "Custom Value".
- **Why:** Essential for preparing data for analysis or export.

### Search and Replace
- **Goal:** `Ctrl+F` style interface to find and replace text within a column or the entire dataset. Support for regex.

### Deduplication
- **Goal:** "Remove Duplicate Rows" action, with options to select which columns to consider for uniqueness.

## VisiData Parity

Bringing the power of VisiData's advanced data manipulation to the web.

### Join Sheets
- **Goal:** UI to join two open sheets based on a common key column (Inner, Left, Right, Outer joins).

### Pivot Tables
- **Goal:** Drag-and-drop interface to create pivot tables (Rows, Columns, Values) from the current dataset.

### Melt/Unpivot
- **Goal:** Transform wide data into long format (and vice versa) with a simple wizard.

### Computed Columns
- **Goal:** Add new columns based on Python expressions involving other columns (e.g., `col_a + col_b * 100`).

## GUI Enhancements

Making the application feel like a native, premium tool.

### Theme Customization
- **Goal:** User-selectable themes (Dark, Light, High Contrast, Custom Colors).

### Better Keyboard Navigation
- **Goal:** Full keyboard control for power users (Vim-style bindings option), ensuring every action is accessible without a mouse.

### Responsive Design
- **Goal:** Better layout adaptation for smaller screens and tablets, including collapsible sidebars and touch-friendly controls.

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
