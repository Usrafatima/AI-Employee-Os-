"""PDF rendering for quotations, invoices and receipts.

One standard template serves all three document types: the same header,
company branding, customer block, item table and totals panel are reused, and
each document type only supplies its own title, metadata and summary rows.
That keeps the three PDFs visually consistent and means a branding change is
made in exactly one place.

Branding (name, logo, address, contact details) comes from settings, so no
company data is hardcoded here.
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from io import BytesIO
from typing import Any, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import settings
from app.services.finance_calculator import money

logger = logging.getLogger(__name__)

# Palette — a restrained navy/slate scheme that prints legibly in greyscale.
BRAND = colors.HexColor("#1e293b")
ACCENT = colors.HexColor("#4f46e5")
MUTED = colors.HexColor("#64748b")
RULE = colors.HexColor("#cbd5e1")
ZEBRA = colors.HexColor("#f8fafc")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN)

_STATUS_COLORS = {
    "paid": colors.HexColor("#047857"),
    "accepted": colors.HexColor("#047857"),
    "partially_paid": colors.HexColor("#b45309"),
    "sent": colors.HexColor("#1d4ed8"),
    "converted": colors.HexColor("#4f46e5"),
    "draft": MUTED,
    "rejected": colors.HexColor("#b91c1c"),
    "cancelled": colors.HexColor("#b91c1c"),
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle", parent=base["Title"], fontSize=22, leading=26,
            textColor=BRAND, alignment=TA_RIGHT, spaceAfter=0,
        ),
        "docmeta": ParagraphStyle(
            "DocMeta", parent=base["Normal"], fontSize=9, leading=13,
            textColor=MUTED, alignment=TA_RIGHT,
        ),
        "company": ParagraphStyle(
            "Company", parent=base["Normal"], fontSize=13, leading=16,
            textColor=BRAND, fontName="Helvetica-Bold",
        ),
        "small": ParagraphStyle(
            "Small", parent=base["Normal"], fontSize=8.5, leading=12, textColor=MUTED,
        ),
        "label": ParagraphStyle(
            "Label", parent=base["Normal"], fontSize=7.5, leading=10,
            textColor=MUTED, fontName="Helvetica-Bold", spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"], fontSize=9.5, leading=13, textColor=BRAND,
        ),
        "cell": ParagraphStyle(
            "Cell", parent=base["Normal"], fontSize=9, leading=12, textColor=BRAND,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["Normal"], fontSize=8, leading=11, textColor=MUTED,
        ),
        # Leading must exceed the font size on both banner styles, otherwise
        # the label and the amount overlap.
        "banner_label": ParagraphStyle(
            "BannerLabel", parent=base["Normal"], fontSize=9, leading=13,
            textColor=colors.white,
        ),
        "banner_amount": ParagraphStyle(
            "BannerAmount", parent=base["Normal"], fontSize=22, leading=27,
            textColor=colors.white, fontName="Helvetica-Bold",
        ),
    }


class _NumberedCanvas(pdfcanvas.Canvas):
    """Canvas that stamps 'Page X of Y' once the total page count is known."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_states: list[dict[str, Any]] = []

    def showPage(self) -> None:  # noqa: N802 - reportlab API
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total_pages: int) -> None:
        self.setStrokeColor(RULE)
        self.setLineWidth(0.5)
        self.line(MARGIN, 14 * mm, PAGE_WIDTH - MARGIN, 14 * mm)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(MUTED)
        if settings.COMPANY_NAME:
            self.drawString(MARGIN, 10 * mm, settings.COMPANY_NAME)
        self.drawRightString(
            PAGE_WIDTH - MARGIN, 10 * mm, f"Page {self.getPageNumber()} of {total_pages}"
        )


def _fmt(value: Any) -> str:
    """Format an amount with the configured currency symbol."""
    return f"{settings.CURRENCY_SYMBOL}{money(value):,.2f}"


def _fmt_qty(value: Any) -> str:
    """Drop trailing zeros so whole quantities read as '3', not '3.000'."""
    quantized = Decimal(str(value)).normalize()
    if quantized == quantized.to_integral_value():
        return str(quantized.to_integral_value())
    return f"{quantized:f}"


def _fmt_date(value: Any) -> str:
    return value.strftime("%d %b %Y") if value else "—"


def _fmt_rate(value: Any) -> str:
    """Render a stored rate without trailing zeros: 17.000 -> '17', 17.500 -> '17.5'.

    ``normalize()`` can return an exponent form (17.000 -> 1.7E+1), so the
    result is formatted with 'f' to force plain notation.
    """
    rate = Decimal(str(value or 0)).normalize()
    return f"{rate:f}"


def _company_logo() -> Image | None:
    path = (settings.COMPANY_LOGO_PATH or "").strip()
    if not path or not os.path.isfile(path):
        return None
    try:
        reader = ImageReader(path)
        source_width, source_height = reader.getSize()
        target_height = 16 * mm
        target_width = target_height * (source_width / float(source_height))
        max_width = 45 * mm
        if target_width > max_width:
            target_width = max_width
            target_height = target_width * (source_height / float(source_width))
        return Image(path, width=target_width, height=target_height)
    except Exception:  # noqa: BLE001 - a broken logo must never block a document
        logger.warning("Could not render company logo at %s; continuing without it.", path)
        return None


def _company_block(style: dict[str, ParagraphStyle]) -> list[Any]:
    lines = [Paragraph(settings.COMPANY_NAME or "Company", style["company"])]
    details = [
        part
        for part in (
            settings.COMPANY_ADDRESS,
            settings.COMPANY_EMAIL,
            settings.COMPANY_PHONE,
            settings.COMPANY_WEBSITE,
            f"Tax No: {settings.COMPANY_TAX_NUMBER}" if settings.COMPANY_TAX_NUMBER else "",
        )
        if part
    ]
    if details:
        lines.append(Paragraph("<br/>".join(details), style["small"]))
    return lines


def _header(title: str, meta_rows: Sequence[tuple[str, str]], style: dict[str, ParagraphStyle]) -> list[Any]:
    left: list[Any] = []
    logo = _company_logo()
    if logo is not None:
        left.append(logo)
        left.append(Spacer(1, 4))
    left.extend(_company_block(style))

    meta_html = "<br/>".join(f"<b>{label}</b>&nbsp;&nbsp;{value}" for label, value in meta_rows)
    right = [Paragraph(title, style["title"]), Spacer(1, 6), Paragraph(meta_html, style["docmeta"])]

    table = Table([[left, right]], colWidths=[CONTENT_WIDTH * 0.55, CONTENT_WIDTH * 0.45])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    rule = Table([[""]], colWidths=[CONTENT_WIDTH], rowHeights=[2])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)]))

    return [table, Spacer(1, 10), rule, Spacer(1, 14)]


def _status_chip(status_value: str, style: dict[str, ParagraphStyle]) -> Table:
    color = _STATUS_COLORS.get(status_value, MUTED)
    label = status_value.replace("_", " ").upper()
    # An explicit width keeps the chip hugging its text. Without it, reportlab
    # expands the nested table to fill the parent cell and the chip becomes a
    # full-width band.
    chip_width = stringWidth(label, "Helvetica-Bold", 7.5) + 16
    chip = Table(
        [[Paragraph(f'<font color="#ffffff" size="7.5"><b>{label}</b></font>', style["cell"])]],
        colWidths=[chip_width],
    )
    chip.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return chip


def _parties(customer: Any, meta: Sequence[tuple[str, Any]], style: dict[str, ParagraphStyle]) -> list[Any]:
    customer_lines = [getattr(customer, "full_name", "") or ""]
    for attr in ("company_name", "address"):
        value = getattr(customer, attr, None)
        if value:
            customer_lines.append(str(value))
    city_country = ", ".join(
        str(v) for v in (getattr(customer, "city", None), getattr(customer, "country", None)) if v
    )
    if city_country:
        customer_lines.append(city_country)
    for attr in ("email", "phone"):
        value = getattr(customer, attr, None)
        if value:
            customer_lines.append(str(value))

    left = [
        Paragraph("BILL TO", style["label"]),
        Paragraph("<br/>".join(customer_lines), style["body"]),
    ]

    right: list[Any] = []
    for label, value in meta:
        right.append(Paragraph(label.upper(), style["label"]))
        right.append(value if isinstance(value, (Table, Paragraph)) else Paragraph(str(value), style["body"]))
        right.append(Spacer(1, 5))

    table = Table([[left, right]], colWidths=[CONTENT_WIDTH * 0.6, CONTENT_WIDTH * 0.4])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [table, Spacer(1, 16)]


def _items_table(items: Sequence[Any], style: dict[str, ParagraphStyle]) -> Table:
    header = ["#", "Description", "Qty", "Unit Price", "Amount"]
    rows: list[list[Any]] = [header]

    for index, item in enumerate(items, start=1):
        rows.append(
            [
                str(index),
                Paragraph(str(item.description), style["cell"]),
                _fmt_qty(item.quantity),
                _fmt(item.unit_price),
                _fmt(item.line_total),
            ]
        )

    widths = [
        CONTENT_WIDTH * 0.06,
        CONTENT_WIDTH * 0.48,
        CONTENT_WIDTH * 0.12,
        CONTENT_WIDTH * 0.17,
        CONTENT_WIDTH * 0.17,
    ]
    table = Table(rows, colWidths=widths, repeatRows=1)

    styling = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
        ("TEXTCOLOR", (0, 1), (-1, -1), BRAND),
    ]
    for row_index in range(2, len(rows), 2):
        styling.append(("BACKGROUND", (0, row_index), (-1, row_index), ZEBRA))

    table.setStyle(TableStyle(styling))
    return table


def _totals_panel(rows: Sequence[tuple[str, str, bool]], style: dict[str, ParagraphStyle]) -> Table:
    """Right-aligned totals block. Each row is (label, value, is_emphasised)."""
    data = [[label, value] for label, value, _ in rows]
    panel_width = CONTENT_WIDTH * 0.42
    table = Table(data, colWidths=[panel_width * 0.55, panel_width * 0.45])

    styling = [
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]
    for index, (_, _, emphasised) in enumerate(rows):
        if emphasised:
            styling.extend(
                [
                    ("BACKGROUND", (0, index), (-1, index), BRAND),
                    ("TEXTCOLOR", (0, index), (-1, index), colors.white),
                    ("FONTNAME", (0, index), (-1, index), "Helvetica-Bold"),
                    ("FONTSIZE", (0, index), (-1, index), 11),
                    ("TOPPADDING", (0, index), (-1, index), 8),
                    ("BOTTOMPADDING", (0, index), (-1, index), 8),
                ]
            )
        else:
            styling.append(("LINEBELOW", (0, index), (-1, index), 0.4, RULE))

    table.setStyle(TableStyle(styling))

    wrapper = Table([["", table]], colWidths=[CONTENT_WIDTH - panel_width, panel_width])
    wrapper.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return wrapper


def _notes(notes: str | None, terms: str | None, style: dict[str, ParagraphStyle]) -> list[Any]:
    blocks: list[Any] = []
    for label, text in (("NOTES", notes), ("TERMS & CONDITIONS", terms)):
        if not text:
            continue
        blocks.extend(
            [
                Spacer(1, 16),
                Paragraph(label, style["label"]),
                Paragraph(str(text).replace("\n", "<br/>"), style["footer"]),
            ]
        )
    return blocks


def _render(story: list[Any], title: str, subject: str) -> bytes:
    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=22 * mm,
        title=title,
        subject=subject,
        author=settings.COMPANY_NAME or "AI Employee OS",
    )
    frame = Frame(MARGIN, 22 * mm, CONTENT_WIDTH, PAGE_HEIGHT - MARGIN - 22 * mm, id="body")
    doc.addPageTemplates([PageTemplate(id="standard", frames=[frame])])
    doc.build(story, canvasmaker=_NumberedCanvas)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------


def build_quotation_pdf(quotation: Any) -> bytes:
    style = _styles()
    customer = quotation.customer

    story: list[Any] = []
    story += _header(
        "QUOTATION",
        [("No.", quotation.quotation_number), ("Date", _fmt_date(quotation.issue_date))],
        style,
    )
    story += _parties(
        customer,
        [
            ("Status", _status_chip(quotation.status, style)),
            ("Valid Until", _fmt_date(quotation.valid_until)),
        ],
        style,
    )
    story.append(_items_table(quotation.items, style))
    story.append(Spacer(1, 14))

    rows = [("Subtotal", _fmt(quotation.subtotal), False)]
    if Decimal(quotation.discount_amount) > 0:
        rows.append(("Discount", f"-{_fmt(quotation.discount_amount)}", False))
    rows.append((f"Tax ({_fmt_rate(quotation.tax_rate)}%)", _fmt(quotation.tax_amount), False))
    rows.append(("Total", _fmt(quotation.grand_total), True))

    story.append(_totals_panel(rows, style))
    story += _notes(quotation.notes, quotation.terms, style)

    return _render(story, f"Quotation {quotation.quotation_number}", "Quotation")


def build_invoice_pdf(invoice: Any) -> bytes:
    style = _styles()
    customer = invoice.customer

    story: list[Any] = []
    story += _header(
        "INVOICE",
        [("No.", invoice.invoice_number), ("Date", _fmt_date(invoice.issue_date))],
        style,
    )

    meta: list[tuple[str, Any]] = [("Status", _status_chip(invoice.status, style))]
    if invoice.due_date:
        meta.append(("Due Date", _fmt_date(invoice.due_date)))
    if invoice.quotation_id and invoice.quotation is not None:
        meta.append(("Quotation Ref", invoice.quotation.quotation_number))
    story += _parties(customer, meta, style)

    story.append(_items_table(invoice.items, style))
    story.append(Spacer(1, 14))

    rows = [("Subtotal", _fmt(invoice.subtotal), False)]
    if Decimal(invoice.discount_amount) > 0:
        rows.append(("Discount", f"-{_fmt(invoice.discount_amount)}", False))
    rows.append((f"Tax ({_fmt_rate(invoice.tax_rate)}%)", _fmt(invoice.tax_amount), False))
    rows.append(("Total", _fmt(invoice.grand_total), True))
    if Decimal(invoice.amount_paid) > 0:
        rows.append(("Amount Paid", f"-{_fmt(invoice.amount_paid)}", False))
        rows.append(("Balance Due", _fmt(invoice.balance_due), True))

    story.append(_totals_panel(rows, style))
    story += _notes(invoice.notes, invoice.terms, style)

    return _render(story, f"Invoice {invoice.invoice_number}", "Invoice")


def build_receipt_pdf(receipt: Any, payment: Any, invoice: Any) -> bytes:
    style = _styles()
    customer = invoice.customer

    story: list[Any] = []
    story += _header(
        "RECEIPT",
        [("No.", receipt.receipt_number), ("Date", _fmt_date(payment.payment_date))],
        style,
    )
    story += _parties(
        customer,
        [("Invoice Ref", invoice.invoice_number), ("Payment Method", payment.method.replace("_", " ").title())],
        style,
    )

    # Two separate paragraphs rather than one with <br/>: a single paragraph
    # uses one leading value for both lines, which makes a 22pt amount collide
    # with the label above it.
    confirmation = Table(
        [
            [Paragraph("AMOUNT RECEIVED", style["banner_label"])],
            [Paragraph(_fmt(payment.amount), style["banner_amount"])],
        ],
        colWidths=[CONTENT_WIDTH],
    )
    confirmation.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BRAND),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (0, 0), 14),
                ("BOTTOMPADDING", (0, 0), (0, 0), 2),
                ("TOPPADDING", (0, 1), (0, 1), 0),
                ("BOTTOMPADDING", (0, 1), (0, 1), 14),
            ]
        )
    )
    story.append(KeepTogether(confirmation))
    story.append(Spacer(1, 18))

    detail_rows = [
        ["Receipt Number", receipt.receipt_number],
        ["Payment Date", _fmt_date(payment.payment_date)],
        ["Payment Method", payment.method.replace("_", " ").title()],
        ["Reference", payment.reference or "—"],
        ["Invoice Number", invoice.invoice_number],
        ["Invoice Total", _fmt(invoice.grand_total)],
    ]
    detail = Table(detail_rows, colWidths=[CONTENT_WIDTH * 0.35, CONTENT_WIDTH * 0.65])
    detail.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("TEXTCOLOR", (1, 0), (1, -1), BRAND),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
            ]
        )
    )
    story.append(detail)
    story.append(Spacer(1, 14))

    story.append(
        _totals_panel(
            [
                ("Invoice Total", _fmt(invoice.grand_total), False),
                ("This Payment", _fmt(payment.amount), False),
                ("Balance Remaining", _fmt(receipt.balance_after), True),
            ],
            style,
        )
    )

    settled = Decimal(receipt.balance_after) <= 0
    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "This invoice is settled in full. Thank you for your business."
            if settled
            else "Partial payment received. The balance above remains outstanding.",
            style["footer"],
        )
    )
    story += _notes(payment.notes, None, style)

    return _render(story, f"Receipt {receipt.receipt_number}", "Payment Receipt")
