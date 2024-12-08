from enum import StrEnum  # python 3.11+

from reportlab.pdfgen import canvas
from pathlib import Path
import pikepdf
from rich import print as rprint


class AllowedFonts(StrEnum):
    Helvetica = "Helvetica"
    Times_Roman = "Times-Roman"
    Courier = "Courier"
    Symbol = "Symbol"
    ZapfDingbats = "ZapfDingbats"


def create_watermark(
    output_pdf: Path,
    text: str,
    page_width: float,
    page_height: float,
    font: str,
    font_size: int,
    rotation: int,
    gray_level: float,
    alpha_level: float,
):
    """
    Creates a single-page watermark PDF with text displayed diagonally.

    :param output_pdf: Path to save the watermark PDF.
    :param text: The text to display as a watermark.
    :param page_width: Width of the page.
    :param page_height: Height of the page.
    :param font: Font name for the watermark text.
    :param font_size: Font size for the watermark text.
    """
    c = canvas.Canvas(str(output_pdf), pagesize=(page_width, page_height))
    c.setFont(font, font_size)  # Set font name and size
    c.setFillGray(gray_level, alpha_level)  # Default: Light gray text
    c.saveState()

    # Translate to the center and rotate for diagonal placement
    c.translate(page_width / 2, page_height / 2)
    c.rotate(rotation)

    # Draw the text at the center of the page
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.save()


def add_watermark(
    target_pdf: Path,
    watermark_text: str,
    overwrite: bool = False,
    font: str = "Helvetica",
    font_size: int = 45,
    rotation: int = 35,
    gray_level: float = 0.5,
    alpha_level: float = 0.5,
):
    """
    Adds a diagonal watermark to each page of the target PDF.

    :param target_pdf: Path to the PDF file to be watermarked.
    :param watermark_text: The text to use as a watermark.
    :param overwrite: Whether to overwrite the input PDF. Default is False.
    :param font: Font name for the watermark text. Default is 'Helvetica'.
    :param font_size: Font size for the watermark text. Default is 40.
    """
    if "_watermarked" in target_pdf.stem:
        rprint(
            f"[yellow]The file '{target_pdf.name}' appears to already be watermarked. Aborting.[/yellow]"
        )
        return

    # Determine the output path
    output_pdf = (
        target_pdf
        if overwrite
        else target_pdf.with_stem(f"{target_pdf.stem}_watermarked")
    )

    with pikepdf.open(target_pdf, allow_overwriting_input=True) as pdf:
        # Get page dimensions from the first page
        first_page = pdf.pages[0]
        page_width = first_page.MediaBox[2]  # Page width
        page_height = first_page.MediaBox[3]  # Page height

        # Generate a temporary watermark file name based on the original file name
        watermark_pdf_path = target_pdf.with_stem(f"{target_pdf.stem}_temp")

        # Create the temporary watermark PDF
        create_watermark(
            output_pdf=watermark_pdf_path,
            text=watermark_text,
            page_width=page_width,
            page_height=page_height,
            font=font,
            font_size=font_size,
            rotation=rotation,
            gray_level=gray_level,
            alpha_level=alpha_level,
        )

        # Open the watermark PDF
        with pikepdf.open(
            watermark_pdf_path, allow_overwriting_input=True
        ) as watermark_pdf:
            watermark_page = watermark_pdf.pages[0]

            # Apply watermark to all pages
            for page in pdf.pages:
                page.add_overlay(watermark_page)

        # Save the watermarked PDF
        pdf.save(output_pdf)

        # Clean up temporary watermark PDF
        watermark_pdf_path.unlink()

    rprint(f"Watermarked PDF saved to: {output_pdf}")


if __name__ == "__main__":
    # Example Usage
    input_pdf = Path("input.pdf")
    output_pdf = Path("output_watermarked.pdf")
    watermark_text = "Copyright (c) 2024 The Author, PhD"

    add_watermark(
        target_pdf=input_pdf,
        output_pdf=output_pdf,
        watermark_text=watermark_text,
        font="Times-Roman",  # Custom font name
        font_size=50,  # Custom font size
    )
