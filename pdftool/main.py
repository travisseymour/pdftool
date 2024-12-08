import typer
from importlib.resources import files
from pathlib import Path
import pikepdf
from datetime import datetime
from rich.console import Console

from pdftool.watermark import add_watermark, AllowedFonts

app = typer.Typer(help="pdftool: A versatile PDF processing tool.")

console = Console()

# Author and year details
AUTHOR = "Travis L. Seymour, PhD."
YEAR = datetime.now().year


def print_startup_message():
    """
    Prints the startup message when the program runs.
    """
    message = f"""
    PDF Tool  Copyright (C) {YEAR}  {AUTHOR}
    This program comes with ABSOLUTELY NO WARRANTY; for the GPLv3 license overview,
    type `pdftool license`. This is free software, and you are welcome to redistribute it
    under certain conditions; type `pdftool full_license` for the full GPLv3 license.
    """
    typer.echo(message)


def shrink_pdf(input_path: Path, output_path: Path):
    """
    Cleans and shrinks a PDF using pikepdf.
    """
    try:
        with pikepdf.open(input_path, allow_overwriting_input=True) as pdf:
            pdf.save(output_path, linearize=True, recompress_flate=True)
    except pikepdf.PdfError as e:
        raise RuntimeError(console.render_str(f"pikepdf failed to process pdf: {e}"))


@app.command("license")
def show_license():
    """
    Prints the full license text from the LICENSE file.
    """
    # Use the package directory to locate the LICENSE file
    try:
        license_file = files("pdftool.resources.text").joinpath("LICENSE")
        typer.echo(license_file.read_text())
    except FileNotFoundError:
        typer.echo(console.render_str("[red]LICENSE file not found.[/red]"), err=True)
        raise typer.Exit(1)


@app.command("full_license")
def show_license():
    """
    Prints the full license text from the LICENSE file.
    """
    # Use the package directory to locate the LICENSE file
    try:
        license_file = files("pdftool.resources.text").joinpath("LICENSE_FULL")
        typer.echo(license_file.read_text())
    except FileNotFoundError:
        typer.echo(
            console.render_str("[red]LICENSE_FULL file not found.[/red]"), err=True
        )
        raise typer.Exit(1)


@app.command("help")
def show_help():
    """
    Displays information about how to use pdftool.
    """
    help_message = """
    pdftool: A versatile PDF processing tool.

    Available commands:
      - shrink [FILE_OR_FOLDER]: Shrink a PDF file or all PDFs in a folder.
      - watermark [FILE_OR_FOLDER TEXT]: Add a watermark to a PDF file or all PDFs in a folder.
      - license: Print the contents of the LICENSE file.
      - full_license: Print the contents of the LICENSE_FULL file.
      - help: Display this help message.

    Examples:
      pdftool shrink my_file.pdf
      pdftool shrink /path/to/folder
      pdftool shrink /path/to/folder --overwrite

      pdftool watermark my_file.pdf "Confidential" --rotation 45 --gray 0.5 --alpha 0.5
      pdftool watermark /path/to/folder "Copyright (c) 2024 The Author, PhD" --font "Times-Roman" --fontsize 50
      pdftool watermark my_file.pdf "Confidential" --overwrite

      pdftool license
      pdftool full_license
    """
    typer.echo(help_message)


@app.command("shrink")
def shrink(
    target: Path = typer.Argument(
        ..., help="Path to a PDF file or folder containing PDFs."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite the original PDF(s)."
    ),
):
    """
    Shrink a PDF file or all PDFs in a folder.
    """
    print_startup_message()

    if target.is_file():
        if target.suffix.lower() != ".pdf":
            typer.echo("The specified file is not a PDF.", err=True)
            raise typer.Exit(1)

        output_file = (
            target if overwrite else target.with_stem(target.stem + "_shrunken")
        )
        shrink_pdf(target, output_file)
        typer.echo(f"Shrunken PDF saved to: {output_file}")

    elif target.is_dir():
        pdf_files = list(target.glob("*.pdf"))
        if not pdf_files:
            typer.echo(
                console.render_str(
                    "[red]No PDF files found in the specified folder.[/red]"
                ),
                err=True,
            )
            raise typer.Exit(1)

        for pdf_file in pdf_files:
            output_file = (
                pdf_file
                if overwrite
                else pdf_file.with_stem(pdf_file.stem + "_shrunken")
            )
            shrink_pdf(pdf_file, output_file)
            typer.echo(f"Shrunken PDF saved to: {output_file}")
    else:
        typer.echo(
            console.render_str(
                "[red]The specified path is neither a file nor a folder.[/red]"
            ),
            err=True,
        )
        raise typer.Exit(1)


@app.command("watermark")
def watermark(
    path: Path = typer.Argument(..., help="Path to a PDF file or a folder of PDFs."),
    text: str = typer.Argument(..., help="Watermark text to apply."),
    rotation: int = typer.Option(35, help="Rotation in degrees."),
    gray: float = typer.Option(
        0.5,
        help="Text gray level (0.0-1.0: 0.0 is white and 1.0 is black)",
        min=0.0,
        max=1.0,
    ),
    alpha: float = typer.Option(
        0.5, help="Text alpha level (0.0-1.0)", min=0.0, max=1.0
    ),
    # font: str = typer.Option("Helvetica", help="Font for the watermark text."),
    font: AllowedFonts = typer.Option(
        AllowedFonts.Helvetica, help="Font for the watermark text."
    ),
    fontsize: int = typer.Option(45, help="Font size for the watermark text."),
    overwrite: bool = typer.Option(False, help="Overwrite the original PDFs."),
):
    """
    Add a watermark to a PDF file or all PDFs in a folder.
    E.g.:
    pdftool watermark myfile.pdf "Copyright (c) 2024 The Author, PhD" --font "Times-Roman" --fontsize 50
    pdftool watermark ./my_pdfs "Copyright (c) 2024 The Author, PhD"
    pdftool watermark myfile.pdf "Confidential" --overwrite
    """
    if path.is_file():
        add_watermark(
            path,
            watermark_text=text,
            overwrite=overwrite,
            font=font,
            font_size=fontsize,
            rotation=rotation,
            gray_level=gray,
            alpha_level=alpha,
        )
    elif path.is_dir():
        for pdf_file in path.glob("*.pdf"):
            add_watermark(
                pdf_file,
                watermark_text=text,
                overwrite=overwrite,
                font=font,
                font_size=fontsize,
                rotation=rotation,
                gray_level=gray,
                alpha_level=alpha,
            )
    else:
        typer.echo(
            console.render_str(
                "[red]The specified path is neither a file nor a folder.[/red]"
            ),
            err=True,
        )
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
