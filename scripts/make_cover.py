import base64, sys, os

# Cover page for the report, from the Premier University Chattogram project-report
# cover template (8th Semester/Cover-Pages/.template/make-project-cover.py).
# The third "submitted to" line is a parameter here instead of the CSE department.
# Output: report/assets/cover.fodt, converted to PDF and DOCX by 07_report.py.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "report", "assets")
LOGO = os.path.join(ASSETS, "puc-logo.png")
b64 = base64.b64encode(open(LOGO, "rb").read()).decode()

HEAD = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">
<office:font-face-decls>
  <style:font-face style:name="Calibri" svg:font-family="Calibri" style:font-family-generic="swiss"/>
  <style:font-face style:name="Times New Roman" svg:font-family="&apos;Times New Roman&apos;" style:font-family-generic="roman"/>
</office:font-face-decls>
<office:automatic-styles>
  <style:page-layout style:name="pm1">
    <style:page-layout-properties fo:page-width="8.268in" fo:page-height="11.693in"
      style:print-orientation="portrait" fo:margin-top="0.3in" fo:margin-bottom="0.6in"
      fo:margin-left="0.79in" fo:margin-right="0.79in"/>
  </style:page-layout>

  <style:style style:name="PLogo" style:family="paragraph">
    <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.18in"/>
  </style:style>
  <style:style style:name="PTitle" style:family="paragraph">
    <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.12in"/>
    <style:text-properties style:font-name="Calibri" fo:font-size="24pt" fo:font-weight="bold"/>
  </style:style>
  <style:style style:name="PDept" style:family="paragraph">
    <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.35in"
      fo:border="0.5pt solid #000000" fo:padding-top="0.10in" fo:padding-bottom="0.10in"
      fo:padding-left="0.06in" fo:padding-right="0.06in"/>
    <style:text-properties style:font-name="Calibri" fo:font-size="10pt" fo:font-weight="bold"/>
  </style:style>
  <style:style style:name="PAssign" style:family="paragraph">
    <style:paragraph-properties fo:text-align="center" fo:margin-top="0.20in" fo:margin-bottom="0.32in"/>
    <style:text-properties style:font-name="Calibri" fo:font-size="22pt" fo:font-weight="bold"
      style:text-underline-style="solid" style:text-underline-width="auto" style:text-underline-color="font-color"/>
  </style:style>

  <style:style style:name="PLabel" style:family="paragraph">
    <style:paragraph-properties fo:text-align="center"/>
    <style:text-properties style:font-name="Calibri" fo:font-size="12pt" fo:font-weight="bold"/>
  </style:style>
  <style:style style:name="PValue" style:family="paragraph">
    <style:paragraph-properties fo:text-align="start"/>
    <style:text-properties style:font-name="Calibri" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="PValueSerif" style:family="paragraph">
    <style:paragraph-properties fo:text-align="start"/>
    <style:text-properties style:font-name="Times New Roman" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="PLeftBold" style:family="paragraph">
    <style:paragraph-properties fo:text-align="start"/>
    <style:text-properties style:font-name="Calibri" fo:font-size="13pt" fo:font-weight="bold"/>
  </style:style>
  <style:style style:name="PCentreBold" style:family="paragraph">
    <style:paragraph-properties fo:text-align="center"/>
    <style:text-properties style:font-name="Calibri" fo:font-size="13pt" fo:font-weight="bold"/>
  </style:style>

  <style:style style:name="TItalic" style:family="text">
    <style:text-properties fo:font-style="italic"/>
  </style:style>
  <style:style style:name="fr1" style:family="graphic">
    <style:graphic-properties style:vertical-pos="middle" style:vertical-rel="text"
      style:horizontal-pos="center" style:horizontal-rel="paragraph" fo:border="none"/>
  </style:style>

  <style:style style:name="Tbl" style:family="table">
    <style:table-properties style:width="6.41in" fo:margin-left="0.18in"
      table:align="left" fo:margin-top="0in"/>
  </style:style>
  <style:style style:name="TblC1" style:family="table-column"><style:table-column-properties style:column-width="1.71in"/></style:style>
  <style:style style:name="TblC2" style:family="table-column"><style:table-column-properties style:column-width="0.61in"/></style:style>
  <style:style style:name="TblC3" style:family="table-column"><style:table-column-properties style:column-width="0.45in"/></style:style>
  <style:style style:name="TblC4" style:family="table-column"><style:table-column-properties style:column-width="3.64in"/></style:style>
  <style:style style:name="TR" style:family="table-row"><style:table-row-properties style:min-row-height="0.28in"/></style:style>
  <style:style style:name="TRbig" style:family="table-row"><style:table-row-properties style:min-row-height="0.33in"/></style:style>
  <style:style style:name="Cell" style:family="table-cell">
    <style:table-cell-properties fo:border="0.5pt solid #000000" style:vertical-align="middle"
      fo:padding-top="0.045in" fo:padding-bottom="0.045in" fo:padding-left="0.07in" fo:padding-right="0.07in"/>
  </style:style>
</office:automatic-styles>
<office:master-styles>
  <style:master-page style:name="Standard" style:page-layout-name="pm1"/>
</office:master-styles>
<office:body><office:text>
'''

TAIL = '''</office:text></office:body></office:document>
'''


def cell(par_style, text, cols=1, rows=1, extra=""):
    span = ""
    if cols > 1:
        span += ' table:number-columns-spanned="%d"' % cols
    if rows > 1:
        span += ' table:number-rows-spanned="%d"' % rows
    body = '<text:p text:style-name="%s">%s</text:p>' % (par_style, text)
    out = '<table:table-cell table:style-name="Cell" office:value-type="string"%s>%s</table:table-cell>' % (span, body)
    out += '<table:covered-table-cell/>' * (cols - 1)
    return out


def covered(n=1):
    return '<table:covered-table-cell/>' * n


def build(name, sid, semester, session, course_name, course_code,
          report_no, date_report, date_submit, teacher, designation, organisation):
    p = []
    p.append('<text:p text:style-name="PLogo">'
             '<draw:frame draw:style-name="fr1" text:anchor-type="as-char" '
             'svg:width="2.60in" svg:height="1.87in" draw:z-index="0">'
             '<draw:image><office:binary-data>%s</office:binary-data></draw:image>'
             '</draw:frame></text:p>' % b64)
    p.append('<text:p text:style-name="PTitle">PREMIER<text:s/> UNIVERSITY<text:s/> CHATTOGRAM</text:p>')
    p.append('<text:p text:style-name="PDept">DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING</text:p>')
    p.append('<text:p text:style-name="PAssign">PROJECT REPORT</text:p>')

    rows = []
    def row(cells, style="TR"):
        rows.append('<table:table-row table:style-name="%s">%s</table:table-row>' % (style, "".join(cells)))

    row([cell("PLabel", "COURSE NAME", cols=2), cell("PValue", course_name, cols=2)])
    row([cell("PLabel", "COURSE CODE", cols=2), cell("PValue", course_code, cols=2)])
    row([cell("PLabel", "PROJECT TITLE", cols=2), cell("PValue", report_no, cols=2)])
    row([cell("PLabel", "DATE OF REPORT", cols=2), cell("PValue", date_report, cols=2)])
    row([cell("PLabel", "DATE OF SUBMISSION", cols=2), cell("PValue", date_submit, cols=2)])
    row([cell("PLeftBold", "SUBMITTED TO", cols=4)])

    teacher_block = ('<table:table-cell table:style-name="Cell" table:number-columns-spanned="4" '
                     'office:value-type="string">'
                     '<text:p text:style-name="PCentreBold">%s</text:p>'
                     '<text:p text:style-name="PCentreBold">%s</text:p>'
                     '<text:p text:style-name="PCentreBold">%s</text:p>'
                     '</table:table-cell>%s' % (teacher, designation, organisation, covered(3)))
    rows.append('<table:table-row table:style-name="TRbig">%s</table:table-row>' % teacher_block)

    row([cell("PLeftBold", "REMARKS", rows=7), cell("PLeftBold", "SUBMITTED BY", cols=3)], "TRbig")
    pairs = [("NAME", name, "PValueSerif"), ("ID", sid, "PValueSerif"),
             ("SEMESTER", semester, "PValue"), ("BATCH", "42nd", "PValue"),
             ("SESSION", session, "PValue"), ("SECTION", "A", "PValue")]
    for label, value, vstyle in pairs:
        row([covered(1), cell("PLeftBold", label, cols=2), cell(vstyle, value)], "TRbig")

    table = ('<table:table table:name="Cover" table:style-name="Tbl">'
             '<table:table-column table:style-name="TblC1"/>'
             '<table:table-column table:style-name="TblC2"/>'
             '<table:table-column table:style-name="TblC3"/>'
             '<table:table-column table:style-name="TblC4"/>'
             '%s</table:table>' % "".join(rows))
    p.append(table)
    return HEAD + "".join(p) + TAIL


COVER = dict(
    semester="8th",
    session="Spring 2026",
    course_name="Internship",
    course_code="CSE 4001",
    report_no="Geographic Transportability of Genome-Based Antibiotic Resistance Prediction "
              "in <text:span text:style-name=\"TItalic\">Mycobacterium tuberculosis</text:span>: "
              "A South Asian Evaluation",
    date_report="14-09-2026",
    date_submit="04-10-2026",
    teacher="Imtiaz Riad",
    designation="Co-Founder",
    organisation="Authentic Four Technology",
)

if __name__ == "__main__":
    out = os.path.join(ASSETS, "cover.fodt")
    open(out, "w").write(build("Rimjhim Dey", "0222220005101039", **COVER))
    print("wrote", out)
