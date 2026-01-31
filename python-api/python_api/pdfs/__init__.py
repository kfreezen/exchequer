from fpdf import FPDF

FONT_SIZE = 11


def _setup_fpdf(
    width,
    height,
    font_family="OldStandardTT-Regular",
    include_font_file=True,
    font_size=FONT_SIZE,
):
    pdf = FPDF(
        unit="pt",
        format=(width, height),
        orientation="P",
    )
    pdf.set_page_background(None)
    pdf.set_margin(0)
    pdf.set_compression(True)
    pdf.add_page()
    if include_font_file:
        pdf.add_font(font_family, "", f"fonts/{font_family}.ttf")
    pdf.set_font(font_family, size=font_size)
    return pdf, width, height
