from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source" / "original-evidence"
BUILD_DIR = ROOT / "build"
TEXT_DIR = ROOT / "bundle-src"


FINAL_FILES = [
    "00 – Statement – Application to Vary Termination Date.pdf",
    "01 – Index of Evidence (READ THIS FIRST).pdf",
    "ACAT Filing Pack 1 – Statement, Index and Form Answers.pdf",
    "ACAT Filing Pack 2 – Medical Hardship Evidence.pdf",
    "ACAT Filing Pack 3 – Financial Capacity, Housing Search and Compliance.pdf",
    "Exhibit A – Rental Applications.pdf",
    "Exhibit B – Payment History & ACAT Compliance.pdf",
    "Exhibit C – Income & Financial Capacity.pdf",
    "Exhibit D – Autism Assessment Appointment.pdf",
    "Exhibit E – Medical Wait Times Evidence.pdf",
    "Exhibit F – Rental Ledger & Lease Documents.pdf",
    "Exhibit G – Supporting Communication.pdf",
    "Exhibit H – Exit Preparation Evidence.pdf",
]


@dataclass(frozen=True)
class ExhibitSpec:
    filename: str
    title: str
    summary: str
    sources: list[str]
    placeholder: bool = False
    notes: list[str] | None = None


def ensure_dirs() -> None:
    BUILD_DIR.mkdir(exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)


def clean_previous_outputs() -> None:
    for name in FINAL_FILES:
        path = ROOT / name
        if path.exists():
            path.unlink()
    if BUILD_DIR.exists():
        for file in BUILD_DIR.iterdir():
            if file.is_file():
                file.unlink()


def styles():
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "BundleTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceAfter=10,
            textColor=colors.black,
        ),
        "heading": ParagraphStyle(
            "BundleHeading",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "BundleBody",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "BundleBullet",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=4,
        ),
    }


def write_text_pdf(input_path: Path, output_path: Path) -> None:
    s = styles()
    story = []
    lines = input_path.read_text(encoding="utf-8").splitlines()

    for raw in lines:
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 3))
            continue
        if line.startswith("[") and line.endswith("]"):
            story.append(Paragraph(line[1:-1], s["heading"]))
            continue
        if line.startswith("- "):
            story.append(Paragraph(f"• {line[2:]}", s["bullet"]))
            continue
        if line[0].isdigit() and ". " in line:
            story.append(Paragraph(line, s["body"]))
            continue
        if ":" in line and not line.startswith("http"):
            label, value = line.split(":", 1)
            story.append(Paragraph(f"<b>{label}:</b>{value}", s["body"]))
            continue
        if not story:
            story.append(Paragraph(line, s["title"]))
        else:
            story.append(Paragraph(line, s["body"]))

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=input_path.stem,
        author="Codex",
    )
    doc.build(story)


def build_cover_page(output_path: Path, title: str, summary: str, notes: Iterable[str]) -> None:
    s = styles()
    story = [
        Paragraph(title, s["title"]),
        Paragraph(summary, s["body"]),
        Spacer(1, 8),
        Paragraph("Included Material", s["heading"]),
    ]
    for note in notes:
        story.append(Paragraph(f"• {note}", s["bullet"]))

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Codex",
    )
    doc.build(story)


def image_to_pdf(image_path: Path, output_path: Path) -> None:
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output_path, "PDF", resolution=200.0)


def append_pdf(writer: PdfWriter, pdf_path: Path) -> None:
    reader = PdfReader(str(pdf_path))
    for page in reader.pages:
        writer.add_page(page)


def combine_pdfs(output_path: Path, inputs: list[Path]) -> None:
    writer = PdfWriter()
    for pdf_path in inputs:
        append_pdf(writer, pdf_path)
    with output_path.open("wb") as f:
        writer.write(f)


def create_placeholder_exhibit(output_path: Path, title: str, summary: str, prompts: list[str]) -> None:
    build_cover_page(output_path, title, summary, prompts)


def build_exhibit(spec: ExhibitSpec) -> None:
    if not spec.placeholder:
        temp_cover = BUILD_DIR / f"{spec.title}.cover.pdf"
        notes = list(spec.notes or [])
        if spec.sources:
            notes.extend([f"Source file: {name}" for name in spec.sources])
        build_cover_page(temp_cover, spec.title, spec.summary, notes)

        writer = PdfWriter()
        append_pdf(writer, temp_cover)

        for name in spec.sources:
            src = SOURCE_DIR / name
            if src.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                temp_image_pdf = BUILD_DIR / f"{src.stem}.pdf"
                image_to_pdf(src, temp_image_pdf)
                append_pdf(writer, temp_image_pdf)
            elif src.suffix.lower() == ".pdf":
                append_pdf(writer, src)

        output_path = ROOT / spec.filename
        with output_path.open("wb") as f:
            writer.write(f)
        return

    create_placeholder_exhibit(
        ROOT / spec.filename,
        spec.title,
        spec.summary,
        list(spec.notes or []),
    )


def main() -> None:
    ensure_dirs()
    clean_previous_outputs()

    write_text_pdf(TEXT_DIR / "statement.txt", ROOT / "00 – Statement – Application to Vary Termination Date.pdf")
    write_text_pdf(TEXT_DIR / "index.txt", ROOT / "01 – Index of Evidence (READ THIS FIRST).pdf")
    write_text_pdf(TEXT_DIR / "online_form_answers.txt", BUILD_DIR / "online_form_answers.pdf")

    exhibits = [
        ExhibitSpec(
            filename="Exhibit A – Rental Applications.pdf",
            title="Exhibit A – Rental Applications",
            summary="Evidence of rental applications and unsuccessful attempts to secure alternative accommodation.",
            sources=[
                "Exhibit A - Rental Applications.png",
                "Unsuccesful_property_emails.pdf",
            ],
        ),
        ExhibitSpec(
            filename="Exhibit B – Payment History & ACAT Compliance.pdf",
            title="Exhibit B – Payment History & ACAT Compliance",
            summary="Payment history, rental ledger records, and backpay material relevant to tenancy compliance.",
            sources=[
                "Exhibit B - Payment History.jpg",
                "Exhibit C5 - Ledger (15 Dec 2023 to 6 Mar 2026).pdf",
                "Exhibit C6 - Proof of Ledger Backpay.pdf",
            ],
            notes=[
                "If available, insert any separate ACAT payment orders or payment-agreement documents after the cover page.",
            ],
        ),
        ExhibitSpec(
            filename="Exhibit C – Income & Financial Capacity.pdf",
            title="Exhibit C – Income & Financial Capacity",
            summary="Income statements, cleaning contract material, and household budget demonstrating affordability.",
            sources=[
                "Exhibit C1 - Income Statement (13 March).pdf",
                "Exhibit C2 - Income Statement (27 March).pdf",
                "Exhibit C3 - Contract Pay Offering.pdf",
                "Exhibit C4 - Family Budget.png",
            ],
        ),
        ExhibitSpec(
            filename="Exhibit D – Autism Assessment Appointment.pdf",
            title="Exhibit D – Autism Assessment Appointment",
            summary="Structured placeholder for the appointment confirmation for the autism assessment scheduled on 31 March 2026.",
            sources=[],
            placeholder=True,
            notes=[
                "Applicant note if original booking confirmation is not yet available.",
                "Child name or initials: [insert]",
                "Provider or clinic: [insert]",
                "Appointment date and time: 31 March 2026 [confirm exact time]",
                "How the booking was confirmed to you: [phone, email, letter, portal, other]",
                "Booking or reference number if known: [insert]",
                "Reason the original booking notice is not attached: [insert]",
                "Replace this page with the actual booking confirmation if it becomes available before filing or hearing.",
                "Only keep statements on this page that are true and can be honestly affirmed by the applicant.",
            ],
        ),
        ExhibitSpec(
            filename="Exhibit E – Medical Wait Times Evidence.pdf",
            title="Exhibit E – Medical Wait Times Evidence",
            summary="Structured placeholder for material showing the long wait time for autism assessment appointments.",
            sources=[],
            placeholder=True,
            notes=[
                "Applicant note if formal wait-time material is not yet available.",
                "Who told you about the likely delay: [provider, clinic, specialist, receptionist, other]",
                "When you were told: [insert date or approximate date]",
                "What you were told about the likely wait if the appointment is missed: [insert exact words as closely as possible]",
                "Whether the advice was given by phone, email, letter, or in person: [insert]",
                "Reason the original written material is not attached: [insert]",
                "Replace this page with provider correspondence, referral wait-list material, or another stronger document if it becomes available before filing or hearing.",
                "Only keep statements on this page that are true and can be honestly affirmed by the applicant.",
            ],
        ),
        ExhibitSpec(
            filename="Exhibit F – Rental Ledger & Lease Documents.pdf",
            title="Exhibit F – Rental Ledger & Lease Documents",
            summary="Lease-related documents and supporting tenancy records.",
            sources=[
                "Exhibit C7 - Contract Agreement (24 March).pdf",
                "Exhibit C8 - Contract Agreement (30 March).pdf",
                "Exhibit C9 - Lease Agreement (31 March).pdf",
            ],
        ),
        ExhibitSpec(
            filename="Exhibit G – Supporting Communication.pdf",
            title="Exhibit G – Supporting Communication",
            summary="Relevant communication regarding the tenancy, extension requests, and housing assistance.",
            sources=[
                "Jenna fruend extension request- 44 Bainbridge Close.pdf",
                "Jenna last minute request desperate.pdf",
                "legal aid Housing assistance.pdf",
            ],
        ),
        ExhibitSpec(
            filename="Exhibit H – Exit Preparation Evidence.pdf",
            title="Exhibit H – Exit Preparation Evidence",
            summary="Structured placeholder for cleaning, moving, storage, or other exit-preparation material.",
            sources=[],
            placeholder=True,
            notes=[
                "Applicant note if external moving or cleaning documents are not yet available.",
                "Removalist enquiries or bookings made: [insert]",
                "Cleaning enquiries or quotes obtained: [insert]",
                "Storage enquiries or arrangements made: [insert]",
                "Current stage of packing and what remains to be done: [insert]",
                "Reason supporting external documents are not attached: [insert]",
                "Replace this page with removalist bookings, cleaning quotes, storage arrangements, packing confirmations, or similar documents if they become available before filing or hearing.",
                "Only keep statements on this page that are true and can be honestly affirmed by the applicant.",
            ],
        ),
    ]

    for exhibit in exhibits:
        build_exhibit(exhibit)

    combine_pdfs(
        ROOT / "ACAT Filing Pack 1 – Statement, Index and Form Answers.pdf",
        [
            BUILD_DIR / "online_form_answers.pdf",
            ROOT / "00 – Statement – Application to Vary Termination Date.pdf",
            ROOT / "01 – Index of Evidence (READ THIS FIRST).pdf",
        ],
    )
    combine_pdfs(
        ROOT / "ACAT Filing Pack 2 – Medical Hardship Evidence.pdf",
        [
            ROOT / "Exhibit D – Autism Assessment Appointment.pdf",
            ROOT / "Exhibit E – Medical Wait Times Evidence.pdf",
        ],
    )
    combine_pdfs(
        ROOT / "ACAT Filing Pack 3 – Financial Capacity, Housing Search and Compliance.pdf",
        [
            ROOT / "Exhibit A – Rental Applications.pdf",
            ROOT / "Exhibit B – Payment History & ACAT Compliance.pdf",
            ROOT / "Exhibit C – Income & Financial Capacity.pdf",
        ],
    )

    for file in BUILD_DIR.iterdir():
        if file.is_file():
            file.unlink()


if __name__ == "__main__":
    main()
