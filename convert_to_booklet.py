#!/usr/bin/env python3
"""
convert_to_booklet.py
---------------
Full booklet preparation pipeline:
  1. Reads bookmarks from input.pdf to build a Contents page
  2. Prepends that Contents page to the document
  3. Pads the total page count up to the next multiple of 4 with blank pages
  4. Imposes the pages for saddle-stitch booklet printing:
       - Pages are reordered and placed two-up on landscape sheets
       - Print duplex (flip on short edge) and fold the stack

Usage:
    python3 convert_to_booklet.py [input.pdf] [output.pdf]
    Defaults: input.pdf -> output.pdf

Dependencies: pypdf, reportlab
    pip install pypdf reportlab
"""

import sys
import io
import copy
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import Destination
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


# ─── Outline extraction ───────────────────────────────────────────────────────

def flatten_outline(outline, reader, depth=0):
    """
    Recursively flatten the PDF outline into a list of
    (depth, title, page_number_1indexed) tuples.
    """
    entries = []
    for item in outline:
        if isinstance(item, list):
            entries.extend(flatten_outline(item, reader, depth + 1))
        elif isinstance(item, Destination):
            title = item.title
            try:
                page_num = reader.get_destination_page_number(item) + 1
            except Exception:
                page_num = None
            entries.append((depth, title, page_num))
    return entries


# ─── Blank page factory ───────────────────────────────────────────────────────

def make_blank_page_pdf(page_width, page_height):
    """Return a single blank page as a pypdf PageObject."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def make_blank_sheet_pdf(sheet_width, sheet_height):
    """Return a blank landscape sheet as a pypdf PageObject."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(sheet_width, sheet_height))
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


# ─── Contents page builder ────────────────────────────────────────────────────

def make_contents_page(entries, page_size):
    """
    Build a Contents page as a PDF in a BytesIO buffer.
    Returns a PdfReader over that buffer.
    Page numbers shown are already offset by +1 for the TOC page itself.
    """
    buf = io.BytesIO()
    page_width, page_height = page_size

    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TOCTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=0.3 * cm,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName="Times-Bold",
    )
    rule_style = ParagraphStyle(
        "Rule",
        parent=styles["Normal"],
        fontSize=1,
        spaceBefore=0,
        spaceAfter=0.5 * cm,
        fontName="Times-Roman",
    )

    entry_styles = []
    page_num_styles = []
    for level in range(5):
        indent = level * 0.6 * cm
        entry_styles.append(ParagraphStyle(
            f"TOCEntry{level}",
            parent=styles["Normal"],
            fontSize=11 - level,
            leftIndent=indent,
            spaceAfter=0.15 * cm,
            textColor=colors.black if level == 0 else colors.HexColor("#333333"),
            fontName="Helvetica-Bold" if level == 0 else "Helvetica",
        ))
        page_num_styles.append(ParagraphStyle(
            f"TOCPageNum{level}",
            parent=styles["Normal"],
            fontSize=11 - level,
            alignment=TA_RIGHT,
            textColor=colors.black if level == 0 else colors.HexColor("#333333"),
            fontName="Helvetica-Bold" if level == 0 else "Helvetica",
        ))

    story = []
    title_name = input("Provide a title for this document -> ")
    story.append(Paragraph(title_name, title_style))
    story.append(Paragraph("<hr/>", rule_style))
    story.append(Spacer(1, 0.2 * cm))

    if not entries:
        story.append(Paragraph("", styles["Normal"]))
    else:
        table_data = []
        for depth, title, page_num in entries:
            level = min(depth, len(entry_styles) - 1)
            indent_spaces = "\u00a0" * (depth * 4)
            left_cell  = Paragraph(f"{indent_spaces}{title}", entry_styles[level])
            right_cell = Paragraph(str(page_num + 1) if page_num else "—", page_num_styles[level])
            table_data.append([left_cell, right_cell])

        tbl = Table(table_data, colWidths=[doc.width - 2 * cm, 2 * cm])
        tbl.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ]))
        story.append(tbl)

    doc.build(story)
    buf.seek(0)
    return PdfReader(buf)


# ─── Imposition ───────────────────────────────────────────────────────────────

def impose_booklet(pages):
    """
    Given a list of pypdf PageObject items (length must be a multiple of 4),
    return a list of landscape sheet PageObjects ready for duplex printing.

    Saddle-stitch sheet order for T total pages:
      Sheet 0 front:  [T,   1]   (left=T,   right=1)
      Sheet 0 back:   [2,   T-1] (left=2,   right=T-1)
      Sheet 1 front:  [T-2, 3]   (left=T-2, right=3)
      Sheet 1 back:   [4,   T-3] (left=4,   right=T-3)
      ...

    Output page order (one PDF page per physical side, for duplex printing):
      front of sheet 0, back of sheet 0, front of sheet 1, back of sheet 1, ...

    Print settings: duplex, flip on SHORT edge.
    """
    T = len(pages)
    assert T % 4 == 0, f"Page count must be a multiple of 4, got {T}"
    n_sheets = T // 4

    # Determine sheet dimensions from first page
    pw = float(pages[0].mediabox.width)
    ph = float(pages[0].mediabox.height)
    sheet_w = 2 * pw
    sheet_h = ph

    def make_sheet(left_page, right_page):
        """Compose two portrait pages onto one landscape sheet."""
        sheet = make_blank_sheet_pdf(sheet_w, sheet_h)
        # Left half: no translation
        sheet.merge_transformed_page(left_page,  Transformation().translate(0,  0))
        # Right half: shift right by one page width
        sheet.merge_transformed_page(right_page, Transformation().translate(pw, 0))
        return sheet

    output_sides = []  # each element is one physical side (= one output PDF page)

    for i in range(n_sheets):
        # Page indices (0-based) for this sheet
        # Front: left = T-1-2i, right = 2i
        # Back:  left = 2i+1,   right = T-2-2i
        front_left_idx  = T - 1 - 2 * i
        front_right_idx = 2 * i
        back_left_idx   = 2 * i + 1
        back_right_idx  = T - 2 - 2 * i

        front = make_sheet(pages[front_left_idx], pages[front_right_idx])
        back  = make_sheet(pages[back_left_idx],  pages[back_right_idx])

        output_sides.append(front)
        output_sides.append(back)

    return output_sides


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    input_path  = sys.argv[1] if len(sys.argv) > 1 else "input.pdf"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output.pdf"

    print(f"Reading: {input_path}")
    reader = PdfReader(input_path)
    original_page_count = len(reader.pages)
    print(f"  Original page count : {original_page_count}")

    # Page dimensions from first content page
    first_page = reader.pages[0]
    page_width  = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    # ── 1. Extract outline ──────────────────────────────────────────────────
    entries = flatten_outline(reader.outline, reader)
    print(f"  Bookmark entries    : {len(entries)}")
    if not entries:
        print("  (No bookmarks found — TOC will note this)")

    # ── 2. Build TOC page ───────────────────────────────────────────────────
    toc_reader      = make_contents_page(entries, (page_width, page_height))
    toc_page_count  = len(toc_reader.pages)
    print(f"  TOC page count      : {toc_page_count}")

    # ── 3. Calculate padding ────────────────────────────────────────────────
    total_before_pad  = toc_page_count + original_page_count
    blank_count       = (4 - total_before_pad % 4) % 4
    total_final       = total_before_pad + blank_count

    print(f"\nPage count breakdown:")
    print(f"  TOC pages           : {toc_page_count}")
    print(f"  Content pages       : {original_page_count}")
    print(f"  Subtotal            : {total_before_pad}")
    print(f"  Blank padding pages : {blank_count}")
    print(f"  Final total pages   : {total_final}")

    sheets = total_final // 4
    print(f"\n{'─'*42}")
    print(f"  Total pages in document : {total_final}")
    print(f"  Sheets of paper needed  : {sheets}")
    print(f"{'─'*42}\n")

    # ── 4. Assemble the logical page list ───────────────────────────────────
    all_pages = []
    for page in toc_reader.pages:
        all_pages.append(page)
    for page in reader.pages:
        all_pages.append(page)

    blank = make_blank_page_pdf(page_width, page_height)
    for _ in range(blank_count):
        all_pages.append(blank)

    assert len(all_pages) == total_final

    # ── 5. Impose for booklet ───────────────────────────────────────────────
    print("Imposing pages for booklet printing...")
    imposed_sides = impose_booklet(all_pages)

    # ── 6. Write output ─────────────────────────────────────────────────────
    writer = PdfWriter()
    for side in imposed_sides:
        writer.add_page(side)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Output written to: {output_path}")
    print(f"  {len(imposed_sides)} imposed sides ({sheets} sheets × 2 sides)")
    print()
    print("Print settings:")
    print("  - Duplex: YES")
    print("  - Flip on: SHORT edge")
    print("  - Then fold the stack in half and staple/bind the spine")


if __name__ == "__main__":
    main()
