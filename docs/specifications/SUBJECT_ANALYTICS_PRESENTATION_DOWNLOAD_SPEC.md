# Subject Analytics — Download Report Feature Specification

**Feature:** Add a dedicated "Download Report" control on the Subject Analytics page (`/subject-analytics/`) that lets teachers download the current filtered analytics as a presentation (PowerPoint `.pptx`) or a document (PDF `.pdf`). A distinct download icon/button with a descriptive tooltip sits adjacent to the existing "Apply Filters" button.

**Status:** Draft Specification  
**Target Page:** `http://127.0.0.1:8000/subject-analytics/`  
**Target File Formats:** `.pptx` (PowerPoint via `python-pptx`) and `.pdf` (via `reportlab` — already available)  
**Authorized Users:** Teachers only (via `@teacher_required` decorator)

---

## 1. Overview

The Subject Analytics page provides teachers with rich, filterable performance data on their assigned students. Currently, the page offers on-screen visualisations (charts, stats cards, trend tables, insight cards) but no mechanism to export this data for offline use, presentations, or sharing with colleagues, school leadership, or parents.

This feature adds a **"Download Report" control** with a visually distinct download icon, placed directly next to the "Apply Filters" button. Teachers choose between **PowerPoint (.pptx)** for presentations and **PDF (.pdf)** for printed reports. The exported file reflects exactly what the teacher sees on screen after applying their chosen filters — every chart, table, insight, and recommendation — with clear labels describing each section for the teacher's reference.

---

## 2. UI / UX Integration

### 2.1 Control Placement

A dedicated download toolbar shall be placed **directly next to the existing "Apply Filters" button** inside the filter `<form>` at line ~1070 of `subject_analytics.html`. The arrangement is:

```html
<div class="form-group ds" style="display:flex;align-items:flex-end;gap:0.5rem;flex-wrap:wrap;">
    <!-- Existing Apply button -->
    <button type="submit" class="btn ds ds-primary ds-block">
        <i class="fas fa-filter"></i> Apply Filters
    </button>

    <!-- New: Download icon with format dropdown -->
    <div class="download-group" style="display:flex;align-items:center;gap:0.25rem;">
        <span class="download-label" style="font-size:var(--ds-text-xs);color:var(--text-muted);white-space:nowrap;">
            <i class="fas fa-download"></i> Download:
        </span>
        <select name="download_format" class="ds" style="padding:0.4rem 0.6rem;font-size:var(--ds-text-sm);border-radius:var(--ds-radius-sm);border:1px solid var(--border-color);background:var(--bg-card);color:var(--text-primary);">
            <option value="pptx">📊 PowerPoint (.pptx)</option>
            <option value="pdf">📄 PDF Report (.pdf)</option>
        </select>
        <button type="submit" name="download" value="1"
                class="btn ds ds-success ds-block"
                title="Generate a downloadable report of the current analytics view. The report includes all charts, statistics, trends, and teacher insights for the currently selected filters.">
            <i class="fas fa-file-export"></i> Export
        </button>
    </div>
</div>
```

### 2.2 Visual Design

| Element | Property | Value |
|---|---|---|
| **Export button** | Label | `Export` |
| | Icon | `fa-file-export` (or `fa-download`) |
| | CSS class | `btn ds ds-success ds-block` |
| | Colour | Green/success (distinct from blue "Apply Filters") |
| | Tooltip | `"Generate a downloadable report of the current analytics view. The report includes all charts, statistics, trends, and teacher insights for the currently selected filters."` |
| **Format dropdown** | Label before dropdown | `Download:` with `fa-download` icon |
| | Options | `📊 PowerPoint (.pptx)`, `📄 PDF Report (.pdf)` |
| | Styling | Compact, inline with button, matching DS design system |
| **Overall layout** | Flex container | `display:flex; align-items:flex-end; gap:0.5rem; flex-wrap:wrap;` |

### 2.3 Teacher-Facing Description

The following descriptive text shall appear below the download controls as a `.form-hint` element, explaining to the teacher what the download contains (visible only when data is present — `{% if total > 0 %}`):

```html
<p class="form-hint" style="margin-top:0.5rem;">
    <i class="fas fa-info-circle" style="color:var(--ds-accent);"></i>
    <strong>Download Report:</strong> Generates a complete summary of the current analytics view.
    The file includes the KPI summary (average, highest, lowest scores, pass rate), score distribution,
    terminal-wise performance trends, subject breakdown, pass/fail ratio, regression trend,
    student trend table, subject strengths/weaknesses, and teacher insights & recommendations
    — all reflecting the filters you have applied above.
    Choose <strong>PowerPoint (.pptx)</strong> for presentations or <strong>PDF (.pdf)</strong> for printed reports.
</p>
```

### 2.4 Loading / Feedback

Since generation may take 1–5 seconds on large datasets:

- The Export button text changes to `Generating…` with a spinner on click (client-side JS).
- The dropdown and buttons are disabled during generation to prevent double-submission.
- Backend returns a `FileResponse` — browser standard download behaviour provides completion feedback.
- **No modal or intermediate page** — the download starts immediately.

### 2.5 Client-Side JS

```javascript
// Inside the form's submit handler or via a click listener
document.querySelector('button[name="download"]').addEventListener('click', function() {
    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…';
    this.disabled = true;
    document.querySelector('select[name="download_format"]').disabled = true;
});
```

---

## 3. Backend Implementation

### 3.1 Detection Logic in `subject_analytics()` View

The existing `subject_analytics()` view (line 7768 in `core/views.py`) shall be modified at its entry point to detect the `download` GET parameter:

```python
def subject_analytics(request):
    teacher = request.teacher

    # If download was requested, handle export
    if request.GET.get("download") == "1":
        download_format = request.GET.get("download_format", "pptx")
        # Build context using the same filter logic
        context = _build_subject_analytics_context(request, teacher)
        if download_format == "pdf":
            return export_subject_analytics_pdf(request, context)
        else:
            return export_subject_analytics_pptx(request, context)

    # … rest of existing view logic …
```

### 3.2 Refactored Context Builder

Create a shared helper `_build_subject_analytics_context(request, teacher)` that contains all the filter-parsing and data-computation logic currently in `subject_analytics()`. Both the HTML view and the export views call this helper.

**Pseudocode:**

```python
def _build_subject_analytics_context(request, teacher):
    """
    Parse GET parameters and build the full analytics context dict.
    Used by the HTML view, PPTX export, and PDF export.
    """
    # … all existing logic from lines 7769–8214 of subject_analytics() …
    # Returns the full context dict that is currently passed to render()
    return context
```

### 3.3 New Module: `core/presentation_export.py`

Create a new dedicated module `core/presentation_export.py` containing:

1. `export_subject_analytics_pptx(request, context)` → returns `HttpResponse` with `.pptx`
2. `export_subject_analytics_pdf(request, context)` → returns `HttpResponse` with `.pdf`

**Function signatures:**

```python
def export_subject_analytics_pptx(request, context: dict) -> HttpResponse:
    """
    Build a PowerPoint presentation from the subject analytics context.
    Returns an HttpResponse with content-type
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'.
    """

def export_subject_analytics_pdf(request, context: dict) -> HttpResponse:
    """
    Build a PDF report from the subject analytics context using ReportLab.
    Returns an HttpResponse with content-type 'application/pdf'.
    """
```

### 3.4 URL Routing

No new URL routes needed. The existing `subject-analytics/` route handles the download via the `download` GET parameter. The form submits via `method="get"` to the same URL, and the view detects the parameter and returns a file response instead of HTML.

### 3.5 Required Dependencies

Add to `requirements.txt`:

```
python-pptx>=0.6.21
```

**Note:** `reportlab` is already available (used in `core/export_utils.py` for smart dashboard PDF export, and imported at line 56 of `core/views.py`). No additional PDF dependency is needed.

---

## 4. Downloadable Content Structure

### 4.1 PowerPoint (.pptx) — Slide Structure (10–12 slides)

The `.pptx` file uses 16:9 widescreen format with the AcadStat colour palette.

| # | Slide Title | Content | Data Source |
|---|---|---|---|
| 1 | **Title Slide** | Report title, filter context subtitle, teacher name, generation date, AcadStat branding | Filters + `request.teacher` |
| 2 | **Executive Summary** | KPI table: Average %, Highest %, Lowest %, Pass Rate, Below-40 count, Analysis Mode | `avg_pct`, `highest_pct`, `lowest_pct`, `pass_rate`, `below_40`, `analysis_mode` |
| 3 | **Score Distribution** | Colour-coded table showing 0–39% (Fail), 40–59%, 60–79%, 80–100% counts | `distribution_chart` |
| 4 | **Terminal Performance** | Table showing average % per terminal, one row per subject, with colour coding | `terminal_wise_chart` |
| 5 | **Subject Breakdown** | Table of all subjects with their average % in the selected/latest terminal, sorted | `subject_breakdown_chart`, `subject_snapshot` |
| 6 | **Pass / Fail Overview** | Pass vs Fail counts displayed as a simple visual table with colour bars | `pass_fail_chart`, `pass_count`, `total` |
| 7 | **Regression Trend** | Trend direction (improving/declining/steady) with slope value in % per terminal | `regression_chart`, `slope` |
| 8 | **Student Trend Table** | Full table: Student Name → marks per terminal → trend arrow (↑↓→) | `trend_rows`, `run_terminals` |
| 9 | **Strengths & Weaknesses** | Strongest subject, weakest subject, count improving/declining/stable | `strongest_subject`, `focus_subject`, `improving_count`, `declining_count`, `stable_count` |
| 10 | **Insights & Recommendations** | Bulleted narrative from the teacher graph summary | `teacher_graph_summary` (headline, graph_reading, achievements, recommendations) |
| 11 | **Detailed Insight Cards** (conditional) | Each enriched insight as a labelled section (strengths, weaknesses, trends, comparisons, recommendations, milestones) | `teacher_enriched_insights` |
| 12 | **Metadata / Footer Slide** | Full filter parameters list, generation timestamp, disclaimer | All filters + datetime |

Every slide includes a **footer text** e.g. `"Filters: Subject=Mathematics | Terminal=2nd | Mode=Bulk | Class=10-A"` in a small text box at the bottom.

### 4.2 PDF (.pdf) — Report Structure (8–10 pages)

The `.pdf` file uses A4 portrait layout generated via ReportLab (already available in the project).

| # | Section | Content | Notes |
|---|---|---|---|
| 1 | **Title Page** | "Subject Analytics Report", teacher name, filter summary, date, AcadStat branding | Full page |
| 2 | **KPI Summary** | Key metrics in a 2×4 grid/table: Average, Highest, Lowest, Pass Rate, Below 40%, Mode, Class/Student | Table format |
| 3 | **Score Distribution** | Distribution bins with counts, visualised as a horizontal bar indicator | Table + mini bar |
| 4 | **Terminal Performance** | Per-terminal averages across subjects | Table |
| 5 | **Subject Snapshot** | Subject-wise performance percentages, strongest/weakest highlighted | Table with colour |
| 6 | **Pass/Fail & Regression** | Pass/fail counts and trend direction description | Text + table |
| 7 | **Student Trend Table** | All students with per-terminal marks and trend direction | Full-width table |
| 8 | **Strengths & Weaknesses** | Summary table of strong/weak subjects and improvement counts | Table |
| 9 | **Teacher Insights** | Headline, graph reading tips, achievements, recommendations as formatted paragraphs | Narrative text |
| 10 | **Appendix / Filters** | Complete filter parameters, generation timestamp, disclaimer | Footer on every page |

**PDF Footer (every page):** `"AcadStat Subject Analytics | Filters: [subject/terminal/mode/class] | Generated: [date]"`

---

## 5. PPTX Implementation Detail

### 5.1 Colour-Coded Tables

For the Score Distribution (Slide 3), each cell uses a background colour proportional to the value:

```
0–39%  (Fail)   →  Red (#EF4444) background
40–59%          →  Amber (#F59E0B) background
60–79%          →  Green (#10B981) background
80–100%         →  Indigo (#6366F1) background
```

For the terminal performance table (Slide 4), cells are colour-coded:
- ≥80% → Green background
- 60–79% → Light green / amber
- 40–59% → Amber
- <40% → Red background

### 5.2 16:9 Widescreen Format

```python
from pptx.util import Inches
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
```

### 5.3 Text Styles

| Element | Font Size | Weight | Colour |
|---|---|---|---|
| Slide title | 28pt | Bold | `#1E293B` |
| Slide subtitle | 16pt | Normal | `#64748B` |
| Table header | 12pt | Bold | White |
| Table cell | 11pt | Normal | `#1E293B` |
| Footer | 9pt | Normal | `#94A3B8` |
| Insight text | 14pt | Normal | `#1E293B` |

---

## 6. PDF Implementation Detail

### 6.1 Reuse Existing ReportLab Infrastructure

The project already uses ReportLab extensively (see `core/export_utils.py` lines 266–457). The PDF export for subject analytics will follow the same pattern:

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
```

### 6.2 PDF Colour Palette

Same palette as PPTX (see Section 11). Uses `colors.HexColor('#XXXXXX')` for ReportLab compatibility.

### 6.3 PDF Layout

- **Page size:** A4 (`reportlab.lib.pagesizes.A4`)
- **Margins:** 1.5cm all sides
- **Title font:** Helvetica-Bold, 18pt, accent colour
- **Body font:** Helvetica, 10pt
- **Table headers:** 9pt, bold, white text on accent background
- **Footer on every page:** 8pt, grey, with filter context

---

## 7. Filter Reflection

**Every page/slide must clearly indicate which filters produced the data.**

- **PPTX:** Footer text box on every slide: `"Filters: Subject=[name/All] | Terminal=[term/All] | Mode=[Bulk/Single] | Class=[section] | Student=[name]"`
- **PDF:** Footer on every page (via `onPage` callback in ReportLab): same format as PPTX footer.
- **Title slide/page:** Full filter context in subtitle.

Active filters to reflect:
| GET Parameter | Display |
|---|---|
| `subject` | Subject name, or "All Subjects" if empty |
| `terminal` | e.g. "2nd Terminal", or "All Terminals" |
| `analysis_mode` | "Bulk Analysis" or "Single Analysis" |
| `class_section` | e.g. "Class 10 — Section A", or "All Sections" |
| `student_id` | Student name (only in single mode) |

---

## 8. File Naming

The downloadable file shall be named dynamically based on active filters and chosen format:

```
SubjectAnalytics_{class_section}_{subject}_{terminal}_{date}.{ext}
```

Examples:
- `SubjectAnalytics_Class10-SecA_Mathematics_2nd_2026-06-30.pptx`
- `SubjectAnalytics_AllClasses_AllSubjects_AllTerminals_2026-06-30.pdf`
- `SubjectAnalytics_Class10-SecA_AllSubjects_1st_2026-06-30.pptx`

Spaces replaced with underscores. Invalid filename characters stripped.

---

## 9. Teacher-Facing Description (Complete Text)

The following text shall appear in the `.form-hint` block below the download controls (Section 2.3):

> **Download Report:** Generates a complete summary of the current analytics view. The file includes the KPI summary (average, highest, lowest scores, pass rate), score distribution, terminal-wise performance trends, subject breakdown, pass/fail ratio, regression trend, student trend table, subject strengths/weaknesses, and teacher insights & recommendations — all reflecting the filters you have applied above. Choose **PowerPoint (.pptx)** for presentations or **PDF (.pdf)** for printed reports.

This description also appears as the **tooltip** on the Export button (title attribute).

---

## 10. Error Handling

| Scenario | Behaviour |
|---|---|
| No data for filters (total = 0) | Return a single-slide/single-page report with "No data available for the selected filters." message |
| Invalid filter values | Treat as per existing behaviour (default to "all") and proceed |
| `python-pptx` import error (PPTX only) | Log error, show user-friendly error message, suggest using PDF instead |
| ReportLab error (PDF only) | Log error, show user-friendly error message |
| Generation timeout (>10s) | Synchronous generation with a 15-second limit is acceptable for v1 |
| Both formats unavailable | Return HTTP 500 with "Report generation unavailable. Please try again later." |

---

## 11. Implementation Checklist

### Backend (Django / Python)

| # | Task | File |
|---|---|---|
| 1 | Add `python-pptx>=0.6.21` to `requirements.txt` | `requirements.txt` |
| 2 | Install `python-pptx` | `pip install python-pptx` |
| 3 | Refactor `subject_analytics()` → extract `_build_subject_analytics_context()` | `core/views.py` |
| 4 | Create `core/presentation_export.py` with both export functions | `core/presentation_export.py` (new) |
| 5 | Implement `export_subject_analytics_pptx()` — all 12 slides | `core/presentation_export.py` |
| 6 | Implement `export_subject_analytics_pdf()` — all 10 sections using ReportLab | `core/presentation_export.py` |
| 7 | Modify `subject_analytics()` to detect `download=1` param and route to export | `core/views.py` |
| 8 | Verify `@teacher_required` decorator protects the download path | `core/views.py` |

### Frontend (Template)

| # | Task | File |
|---|---|---|
| 9 | Replace single button with download group (label + dropdown + export button) next to "Apply Filters" | `subject_analytics.html` (~line 1070) |
| 10 | Add `.form-hint` description text below the download controls | `subject_analytics.html` |
| 11 | Add CSS for download-group inline layout | `subject_analytics.html` |
| 12 | Add JS for loading state on Export button click + disable dropdown | `subject_analytics.html` |

### Testing

| # | Task |
|---|---|
| 13 | Test PPTX download with "All subjects, all terminals, bulk mode" |
| 14 | Test PPTX download with specific subject + single terminal + class section |
| 15 | Test PPTX download with single analysis mode for individual student |
| 16 | Test PDF download with the same filter combinations |
| 17 | Test both formats with no data (total = 0) |
| 18 | Verify all slides/pages contain correct filter context in footer |
| 19 | Verify Content-Disposition filename matches format (`.pptx` vs `.pdf`) |
| 20 | Test `.pptx` opens in Microsoft PowerPoint, LibreOffice Impress, and Google Slides |
| 21 | Test `.pdf` opens in Adobe Acrobat, browser PDF viewer, and mobile PDF readers |
| 22 | Verify the descriptive hint text renders correctly below the download controls |
| 23 | Verify tooltip on Export button shows the full description |

---

## 12. Future Enhancements (Out of Scope for v1)

- Email the report directly to the teacher's registered email.
- Schedule automatic weekly report generation and email delivery.
- Include individual student detail pages/slides for each student in the filtered set.
- Add Excel (.xlsx) as a third export format.
- Real native PowerPoint charts (editable) using `python-pptx` chart API.
- Multi-language support for report content.
- Drag-and-drop reordering of report sections before download.

---

## 13. Appendix: Colour Palette

| Element | Hex Colour | Usage |
|---|---|---|
| Primary accent | `#4F46E5` | Headers, title backgrounds, KPI emphasis |
| Success | `#10B981` | Pass indicators, positive trends, 60–79% cells |
| Danger | `#EF4444` | Fail indicators (below 40%), negative trends |
| Warning | `#F59E0B` | Moderate scores (40–59%) |
| Info | `#3B82F6` | Secondary metrics, information text |
| Excellence | `#6366F1` | 80–100% score cells |
| Text primary | `#1E293B` | Body text |
| Text secondary | `#64748B` | Subtitles, footnotes |
| Background | `#FFFFFF` | Slide/page backgrounds |
| Header bg | `#EEF2FF` | Table header row backgrounds |
| Chart palette | `['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16']` | Same as web chart colours |

---

## 14. Appendix: Quick Reference — PPTX Generation

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import io

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

slide_layout = prs.slide_layouts[6]  # blank layout

def add_title(slide, text, left=0.5, top=0.3, width=12, height=1):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.text = text
    for para in tf.paragraphs:
        para.font.size = Pt(28)
        para.font.bold = True
        para.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    return tf

def add_table(slide, rows, cols, data, left=0.5, top=1.5, width=12, height=4):
    table_shape = slide.shapes.add_table(rows, cols, Inches(left), Inches(top), Inches(width), Inches(height))
    table = table_shape.table
    for r_idx, row_data in enumerate(data):
        for c_idx, cell_text in enumerate(row_data):
            cell = table.cell(r_idx, c_idx)
            cell.text = str(cell_text)
            if r_idx == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0x4F, 0x46, 0xE5)
    return table

def add_footer(slide, text, left=0.5, top=7.0, width=12, height=0.3):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.text = text
    for para in tf.paragraphs:
        para.font.size = Pt(9)
        para.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

def add_slide(title_text, footer_text):
    slide = prs.slides.add_slide(slide_layout)
    add_title(slide, title_text)
    add_footer(slide, footer_text)
    return slide

# Save
buf = io.BytesIO()
prs.save(buf)
buf.seek(0)

response = HttpResponse(
    buf.read(),
    content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
)
response['Content-Disposition'] = f'attachment; filename="{filename}.pptx"'
return response
```

---

## 15. Appendix: Quick Reference — PDF Generation

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

def export_subject_analytics_pdf(request, context):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        title='Subject Analytics Report',
    )
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Subject Analytics Report", styles['Title']))
    elements.append(Paragraph(f"Teacher: {context.get('teacher_name', 'N/A')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # KPI Table
    kpi_data = [
        ['Metric', 'Value'],
        ['Average Score', f"{context.get('avg_pct', 0)}%"],
        ['Highest Score', f"{context.get('highest_pct', 0)}%"],
        ['Lowest Score', f"{context.get('lowest_pct', 0)}%"],
        ['Pass Rate', f"{context.get('pass_rate', 0)}%"],
    ]
    kpi_table = Table(kpi_data)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(kpi_table)

    doc.build(elements)
    buf.seek(0)

    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response