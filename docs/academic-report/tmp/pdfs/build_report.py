"""Build the full academic report with real vector diagrams and typeset equations."""
import html
import json
import math
import re
from pathlib import Path

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, LongTable, PageBreak, PageTemplate,
    Paragraph, Spacer, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
FOLDER = HERE.parents[1]
ROOT = FOLDER.parents[1]
OUTPUT = FOLDER / "output/pdf/NeuroCare-AI-Complete-Academic-Report.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
DOCUMENTS = json.loads((HERE / "parsed-documents.json").read_text(encoding="utf-8"))
rl_config.warnOnMissingFontGlyphs = 1

FONTS = Path("C:/Windows/Fonts")
for name, file in (("Body", "calibri.ttf"), ("Body-Bold", "calibrib.ttf"),
                   ("Body-Italic", "calibrii.ttf"), ("Body-BoldItalic", "calibriz.ttf"),
                   ("Display", "georgia.ttf"), ("Display-Italic", "georgiai.ttf"),
                   ("Mono", "consola.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-BoldItalic")

INK = colors.HexColor("#211C2A")
MUTED = colors.HexColor("#625C6B")
ACCENT = colors.HexColor("#604793")
PALE = colors.HexColor("#F5F1FA")
LAVENDER = colors.HexColor("#E9E1F5")
LINE = colors.HexColor("#DDD5E6")
W, H = A4
MARGIN = 45
WIDTH = W - MARGIN * 2

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("ReportBody", fontName="Body", fontSize=10.1, leading=14.4,
                         textColor=INK, spaceAfter=8.5, allowWidows=0, allowOrphans=0))
styles.add(ParagraphStyle("PartTitle", parent=styles["ReportBody"], fontName="Display",
                         fontSize=25, leading=30, spaceBefore=6, spaceAfter=19,
                         keepWithNext=True))
styles.add(ParagraphStyle("SectionTitle", parent=styles["ReportBody"], fontName="Body-Bold",
                         fontSize=15.5, leading=19, spaceBefore=19, spaceAfter=9,
                         keepWithNext=True))
styles.add(ParagraphStyle("SubsectionTitle", parent=styles["ReportBody"], fontName="Body-Bold",
                         fontSize=11.8, leading=15.5, spaceBefore=13, spaceAfter=6,
                         keepWithNext=True))
styles.add(ParagraphStyle("Cell", parent=styles["ReportBody"], fontSize=8.8, leading=12.2,
                         spaceAfter=0, splitLongWords=True))
styles.add(ParagraphStyle("CellHead", parent=styles["Cell"], fontName="Body-Bold", textColor=ACCENT))
styles.add(ParagraphStyle("Equation", parent=styles["ReportBody"], fontSize=10.8, leading=17,
                         leftIndent=13, rightIndent=10, spaceBefore=4, spaceAfter=10,
                         backColor=PALE, borderPadding=9))
styles.add(ParagraphStyle("ReportCode", parent=styles["ReportBody"], fontName="Mono", fontSize=8.2,
                         leading=11.6, backColor=PALE, borderPadding=9,
                         leftIndent=10, rightIndent=10, spaceBefore=4, spaceAfter=12,
                         splitLongWords=True))
styles.add(ParagraphStyle("Caption", parent=styles["ReportBody"], fontSize=9, leading=12.5,
                         textColor=MUTED, spaceBefore=6, spaceAfter=12))
styles.add(ParagraphStyle("Kicker", parent=styles["ReportBody"], fontName="Body-Bold", fontSize=9,
                         leading=12, textColor=ACCENT, spaceAfter=7))
styles.add(ParagraphStyle("TOC0", fontName="Body-Bold", fontSize=10.6, leading=14,
                         leftIndent=0, firstLineIndent=0, spaceBefore=5, textColor=INK))
styles.add(ParagraphStyle("TOC1", fontName="Body", fontSize=9.2, leading=12,
                         leftIndent=15, firstLineIndent=0, spaceBefore=0, textColor=MUTED))


def clean(text):
    return text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", " - ")


def esc(text):
    return html.escape(clean(str(text)), quote=False)


def math_markup(tex):
    """Linear mathematical typography with real subscripts/superscripts, not raw TeX."""
    mapping = {r"\mu": "μ", r"\sigma": "σ", r"\lambda": "λ", r"\theta": "θ",
               r"\alpha": "α", r"\beta": "β", r"\phi": "φ", r"\epsilon": "ε",
               r"\nabla": "∇", r"\geq": "≥", r"\lVert": "||", r"\rVert": "||"}
    t = tex
    t = re.sub(r"\\(?:mathrm|operatorname|mathcal)\{([^{}]+)\}", r"\1", t)
    t = t.replace(r"\hat m", "m̂").replace(r"\hat v", "v̂").replace(r"\hat y", "ŷ")
    # Simple nested-free fractions used by inline equations.
    while re.search(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", t):
        t = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", t)
    t = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", t)
    for source, replacement in mapping.items():
        t = t.replace(source, replacement)
    t = t.replace(r"\log", "log ").replace(r"\max", "max").replace(r"\sum", "Σ")
    t = t.replace(r"\left", "").replace(r"\right", "").replace(r"\qquad", "   ").replace(r"\quad", "   ")
    t = esc(t)
    t = re.sub(r"_\{([^{}]+)\}", r"<sub>\1</sub>", t)
    t = re.sub(r"\^\{([^{}]+)\}", r"<super>\1</super>", t)
    t = re.sub(r"_([a-zA-Z0-9θβα])", r"<sub>\1</sub>", t)
    t = re.sub(r"\^([0-9])", r"<super>\1</super>", t)
    return t.replace("{", "").replace("}", "")


BLOCKS = [
    'z<sub>j</sub> = (x<sub>j</sub> - μ<sub>j,train</sub>) / σ<sub>j,train</sub>',
    '(21 + 1) × 64 + (64 + 1) × 32 + (32 + 1) × 1 = <b>3,521</b>',
    'h<sub>1</sub> = ReLU(W<sub>1</sub>z + b<sub>1</sub>)<br/>h<sub>2</sub> = ReLU(W<sub>2</sub>h<sub>1</sub> + b<sub>2</sub>)',
    's = σ(W<sub>3</sub>h<sub>2</sub> + b<sub>3</sub>)<br/>ReLU(u) = max(0, u);  σ(u) = 1 / (1 + e<super>-u</super>)',
    'ŷ = 1 if s ≥ 0.132127583026886<br/>ŷ = 0 if s &lt; 0.132127583026886',
    'L = -(1/B) Σ<sub>i=1…B</sub> [y<sub>i</sub> log s<sub>i</sub> + (1 - y<sub>i</sub>) log(1 - s<sub>i</sub>)]<br/>'
    '      + λ (||W<sub>1</sub>||<sub>F</sub><super>2</super> + ||W<sub>2</sub>||<sub>F</sub><super>2</super>),  λ = 10<super>-4</super>',
    'g<sub>t</sub> = ∇<sub>θ</sub>L<sub>t</sub><br/>'
    'm<sub>t</sub> = β<sub>1</sub>m<sub>t-1</sub> + (1 - β<sub>1</sub>)g<sub>t</sub><br/>'
    'v<sub>t</sub> = β<sub>2</sub>v<sub>t-1</sub> + (1 - β<sub>2</sub>)g<sub>t</sub><super>2</super>',
    'θ<sub>t+1</sub> = θ<sub>t</sub> - α<sub>t</sub> m̂<sub>t</sub> / (√(v̂<sub>t</sub>) + ε)',
    'W<sub>n</sub> = diag(σ<sub>n</sub> / σ<sub>o</sub>) W<sub>o</sub><br/>'
    'b<sub>n</sub> = b<sub>o</sub> + ((μ<sub>n</sub> - μ<sub>o</sub>) / σ<sub>o</sub>) W<sub>o</sub>',
    'Accuracy = (TP + TN) / N<br/>Precision = TP / (TP + FP);  Recall = TP / (TP + FN)',
    'F<sub>1</sub> = 2TP / (2TP + FP + FN) = 10,376 / 23,683 = <b>0.438120</b><br/>Specificity = TN / (TN + FP)',
    'F<sub>β</sub> = (1 + β<super>2</super>)PR / (β<super>2</super>P + R)<br/>Brier = (1/N) Σ<sub>i</sub>(s<sub>i</sub> - y<sub>i</sub>)<super>2</super>',
]


class Diagram(Flowable):
    def __init__(self, kind):
        super().__init__()
        self.kind, self.width = kind, WIDTH
        self.height = {"architecture": 325, "sequence": 355, "model": 355}[kind]

    def box(self, x, y, w, h, label, emphasis=False):
        c = self.canv
        c.setFillColor(LAVENDER if emphasis else colors.white)
        c.setStrokeColor(LINE)
        c.roundRect(x, y, w, h, 7, fill=1, stroke=1)
        lines = label.split("\n")
        c.setFillColor(INK)
        c.setFont("Body-Bold" if emphasis else "Body", 9.5)
        for i, line in enumerate(lines):
            c.drawCentredString(x + w / 2, y + h / 2 + (len(lines) - 1) * 5.6 - i * 11.2 - 3, line)

    def arrow(self, points, dashed=False):
        c = self.canv
        c.setStrokeColor(ACCENT)
        c.setFillColor(ACCENT)
        c.setLineWidth(1)
        c.setDash(3, 2) if dashed else c.setDash()
        path = c.beginPath()
        path.moveTo(*points[0])
        for point in points[1:]: path.lineTo(*point)
        c.drawPath(path)
        c.setDash()
        start, end = points[-2], points[-1]
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        path = c.beginPath()
        path.moveTo(*end)
        for delta in (-0.45, 0.45):
            path.lineTo(end[0] - 5 * math.cos(angle + delta), end[1] - 5 * math.sin(angle + delta))
        path.close()
        c.drawPath(path, fill=1, stroke=0)

    def draw(self):
        c = self.canv
        c.setFillColor(PALE)
        c.roundRect(0, 0, self.width, self.height, 10, fill=1, stroke=0)
        if self.kind == "architecture": self.architecture()
        elif self.kind == "sequence": self.sequence()
        else: self.model()

    def architecture(self):
        c = self.canv
        w, h = 142, 38
        mid, left, right = (WIDTH - w) / 2, 14, WIDTH - w - 14
        center = mid + w / 2
        self.box(mid, 269, w, h, "React / TypeScript\nBrowser interface", True)
        self.box(mid, 206, w, h, "FastAPI\nRoutes and strict validation", True)
        self.box(mid, 143, w, h, "Prediction service")
        self.box(left, 78, w, h, "Cached ANN predictor")
        self.box(mid, 78, w, h, "SQLAlchemy repository")
        self.box(right, 78, w, h, "PostgreSQL\nneurocare_db", True)
        self.box(left, 13, w, h, "Versioned model\nand preprocessing")
        self.box(mid, 13, w, h, "Offline data preparation\nand model training")
        self.arrow([(center, 269), (center, 244)])
        self.arrow([(center, 206), (center, 181)])
        self.arrow([(center, 143), (center, 116)])
        self.arrow([(mid + 18, 143), (mid + 18, 130), (left + w / 2, 130), (left + w / 2, 116)])
        self.arrow([(mid + w, 97), (right, 97)])
        self.arrow([(left + w / 2, 51), (left + w / 2, 78)])
        self.arrow([(mid, 32), (left + w, 32)])

    def sequence(self):
        c = self.canv
        names = ["React UI", "FastAPI / service", "Predictor", "Repository", "PostgreSQL"]
        xs = [(i + .5) * WIDTH / 5 for i in range(5)]
        for x, name in zip(xs, names):
            self.box(x - 46, 310, 92, 29, name, True)
            c.setStrokeColor(LINE); c.setDash(2, 3)
            c.line(x, 30, x, 310); c.setDash()
        messages = [(0, 1, "POST 21 features"), (1, 2, "Validate; infer"),
                    (2, 1, "Class, score, version"), (1, 3, "Save inputs/output"),
                    (3, 4, "INSERT + COMMIT"), (4, 3, "Committed row"),
                    (3, 4, "Refresh record"), (4, 3, "Saved ID/fields"),
                    (3, 1, "Saved record"), (1, 0, "201 + result/notice")]
        for index, (a, b, label) in enumerate(messages):
            y = 285 - index * 24
            self.arrow([(xs[a], y), (xs[b], y)], dashed=b < a)
            c.setFont("Body", 8.6); c.setFillColor(INK)
            c.drawCentredString((xs[a] + xs[b]) / 2, y + 5, label)
        c.setFillColor(MUTED); c.setFont("Body", 9)
        c.drawCentredString(WIDTH / 2, 16, "A success follows commit. Errors return 422/503; a response can be lost after a save.")

    def model(self):
        c = self.canv
        w, h, mid = 178, 38, (WIDTH - 178) / 2
        x = WIDTH / 2
        self.box(mid, 298, w, h, "21 validated integer features", True)
        self.box(mid, 232, w, h, "Training-only standardization")
        self.box(10, 165, 128, 45, "Saved model bundle\nweights, scales and cutoff")
        self.box(mid, 165, w, 45, "64 ReLU → 32 ReLU\n→ sigmoid score", True)
        self.box(mid, 100, w, h, "Score ≥ saved cutoff?")
        self.box(65, 40, 143, h, "No: dataset label 0")
        self.box(WIDTH - 208, 40, 143, h, "Yes: dataset label 1")
        self.arrow([(x, 298), (x, 270)])
        self.arrow([(x, 232), (x, 210)])
        self.arrow([(x, 165), (x, 138)])
        self.arrow([(138, 189), (mid, 189)])
        self.arrow([(74, 210), (74, 251), (mid, 251)])
        self.arrow([(x - 26, 100), (x - 26, 88), (136.5, 88), (136.5, 78)])
        self.arrow([(x + 26, 100), (x + 26, 88), (WIDTH - 136.5, 88), (WIDTH - 136.5, 78)])
        c.setFont("Body", 9); c.setFillColor(MUTED)
        c.drawCentredString(x, 16, "Cutoff = 0.132127583026886. Dropout is disabled during inference.")


class Cover(Flowable):
    def __init__(self):
        super().__init__()
        self.width, self.height = WIDTH, 665

    def draw(self):
        c = self.canv
        c.setFillColor(LAVENDER); c.roundRect(0, 173, WIDTH, 475, 14, fill=1, stroke=0)
        c.setFillColor(ACCENT); c.rect(28, 583, 42, 4, fill=1, stroke=0)
        c.setFont("Body-Bold", 10); c.drawString(28, 554, "UNIVERSITY PROJECT DOCUMENTATION")
        c.setFillColor(INK); c.setFont("Display", 43)
        c.drawString(26, 466, "NeuroCare AI")
        c.setFont("Display", 27); c.drawString(28, 419, "Complete Academic Report")
        c.setFont("Body", 13); c.setFillColor(MUTED)
        for y, line in [(366, "System architecture, data preparation and ANN methodology"),
                        (345, "Measured results, implementation and responsible use")]: c.drawString(29, y, line)
        c.setStrokeColor(colors.HexColor("#CFC1E1")); c.line(28, 310, WIDTH - 28, 310)
        c.setFont("Body-Bold", 10); c.setFillColor(ACCENT); c.drawString(29, 278, "ONE DOCUMENT / THREE COMPLETE REPORTS")
        c.setFont("Body", 11); c.setFillColor(INK)
        c.drawString(29, 251, "Full project report + architecture guide + technical quick reference")
        c.drawString(29, 229, "Evidence date: 29 October 2026")
        p = Paragraph("<b>Educational use only.</b> The model classifies historical survey labels. "
                      "Its output is not a medical diagnosis, validated screening result or personal risk estimate.", styles["ReportBody"])
        p.wrap(WIDTH - 16, 100); p.drawOn(c, 8, 91)
        c.setFont("Body", 9); c.setFillColor(MUTED)
        c.drawString(8, 44, "Student, institution, course and supervisor details were not supplied.")
        c.drawString(8, 29, "Add the required administrative information before university submission.")


class NumberedCanvas(Canvas):
    def __init__(self, *args, total_pages=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_pages = total_pages

    def showPage(self):
        # Write each page normally: replaying saved canvas states would corrupt bookmarks.
        if self._pageNumber > 1:
            self.saveState()
            self.setStrokeColor(LINE); self.setLineWidth(.5)
            self.line(MARGIN, 35, W - MARGIN, 35)
            self.setFillColor(MUTED); self.setFont("Body", 8)
            self.drawString(MARGIN, 23, "NeuroCare AI | Academic documentation")
            self.drawRightString(W - MARGIN, 23, f"Page {self._pageNumber} of {self.total_pages}")
            self.restoreState()
        Canvas.showPage(self)


class Document(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(str(path), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=49, bottomMargin=49, title="NeuroCare AI - Complete Academic Report",
                         author="NeuroCare AI Project", subject="Full academic report, architecture and algorithm reference")
        frame = Frame(MARGIN, 49, WIDTH, H - 98, id="body", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="normal", frames=[frame], onPage=self.header))

    def header(self, c, doc):
        if doc.page == 1: return
        c.saveState(); c.setFont("Body-Bold", 8); c.setFillColor(ACCENT)
        c.drawString(MARGIN, H - 29, "NEUROCARE AI")
        c.setFont("Body", 8); c.setFillColor(MUTED)
        c.drawRightString(W - MARGIN, H - 29, "Full project report and appendices")
        c.restoreState()

    def afterFlowable(self, flow):
        if not hasattr(flow, "anchor"): return
        self.canv.bookmarkPage(flow.anchor)
        self.canv.addOutlineEntry(flow.title, flow.anchor, level=flow.outline_level, closed=False)
        if flow.outline_level <= 1:
            self.notify("TOCEntry", (flow.outline_level, esc(flow.title), self.page, flow.anchor))


class Renderer:
    def __init__(self):
        self.story, self.count, self.current_section = [], 0, ""
        self.document = None
        self.lists, self.pending_bullet = [], None

    def inline(self, children):
        output, links = [], []
        for item in children or []:
            kind, value = item["type"], item["content"]
            if kind == "text":
                text = esc(value)
                text = re.sub(r"NCINLINEMATH(\d{3})", lambda m: math_markup(self.document["inline_math"][int(m.group(1))]), text)
                output.append(text)
            elif kind == "code_inline": output.append(f'<font name="Mono" size="8.0">{esc(value)}</font>')
            elif kind == "strong_open": output.append("<b>")
            elif kind == "strong_close": output.append("</b>")
            elif kind == "em_open": output.append("<i>")
            elif kind == "em_close": output.append("</i>")
            elif kind == "hardbreak": output.append("<br/>")
            elif kind == "softbreak": output.append(" ")
            elif kind == "link_open":
                target = item["attrs"].get("href", "")
                if target.startswith(("http://", "https://")):
                    output.append(f'<link href="{html.escape(target, quote=True)}" color="#604793"><u>')
                    links.append(("external", target))
                elif target in {"project-report.md", "architecture.md", "technology-and-algorithm-reference.md"}:
                    anchor = {"project-report.md": "part-report", "architecture.md": "appendix-architecture", "technology-and-algorithm-reference.md": "appendix-reference"}[target]
                    output.append(f'<link href="#{anchor}" color="#604793">')
                    links.append(("internal", target))
                else: links.append(("local", target))
            elif kind == "link_close":
                category, target = links.pop()
                if category == "external":
                    output.append("</u></link>")
                    if self.current_section.startswith("14.2"):
                        output.append(f'<br/><font size="8.5" color="#625C6B">{esc(target)}</font>')
                elif category == "internal": output.append("</link>")
                else:
                    local = (FOLDER / target).resolve()
                    try: shown = local.relative_to(ROOT).as_posix()
                    except ValueError: shown = target
                    output.append(f' <font size="8" color="#625C6B">[{esc(shown)}]</font>')
            elif kind == "html_inline": output.append(value if value in ("<br>", "<br/>") else esc(value))
        return "".join(output)

    def heading(self, children, level, part=None):
        plain = "".join(item["content"] for item in children or [] if item["type"] in ("text", "code_inline"))
        if level == 1:
            title, anchor = part
            style, outline = "PartTitle", 0
        else:
            title, style, outline = plain, "SectionTitle" if level == 2 else "SubsectionTitle", level - 1
            self.count += 1
            anchor = f"section-{self.count:03d}"
            self.current_section = plain
        paragraph = Paragraph(esc(title), styles[style])
        paragraph.anchor, paragraph.title, paragraph.outline_level = anchor, title, outline
        self.story.append(paragraph)

    def table(self, tokens, index):
        rows, row, header, headers = [], [], False, []
        j = index + 1
        while tokens[j]["type"] != "table_close":
            item = tokens[j]
            if item["type"] == "tr_open": row = []
            elif item["type"] == "thead_open": header = True
            elif item["type"] == "thead_close": header = False
            elif item["type"] == "inline":
                row.append(Paragraph(self.inline(item["children"]), styles["CellHead" if header else "Cell"]))
                if header: headers.append(item["content"])
            elif item["type"] == "tr_close": rows.append(row)
            j += 1
        n = len(rows[0])
        if n == 2: ratios = [.29, .71] if headers[0] == "Term" else [.34, .66]
        elif n == 3:
            ratios = [.23, .25, .52] if headers[0] in ("Technology", "Layer") else [.27, .48, .25] if headers[0] == "Feature" else [.28, .22, .50]
        elif n == 4: ratios = [.34, .22, .22, .22]
        elif n == 5:
            ratios = [.40, .15, .15, .15, .15] if "Model/policy" in headers[0] else [.25, .14, .16, .16, .29]
        else: ratios = [1 / n] * n
        table = LongTable(rows, colWidths=[WIDTH * r for r in ratios], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, 0), LAVENDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
            ("LINEBELOW", (0, 0), (-1, 0), .7, LINE),
            ("LINEBELOW", (0, 1), (-1, -1), .3, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5 if headers[0] == "Term" else 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5 if headers[0] == "Term" else 6),
        ]))
        self.story.extend([table, Spacer(1, 10)])
        return j + 1

    def render(self, name, part):
        self.document = DOCUMENTS[name]
        tokens, i = self.document["tokens"], 0
        while i < len(tokens):
            item, kind = tokens[i], tokens[i]["type"]
            if kind == "heading_open":
                self.heading(tokens[i + 1]["children"], int(item["tag"][1:]), part)
                i += 3; continue
            if kind == "table_open":
                i = self.table(tokens, i); continue
            if kind in ("bullet_list_open", "ordered_list_open"):
                self.lists.append({"ordered": kind == "ordered_list_open", "count": item["attrs"].get("start", 1)})
            elif kind in ("bullet_list_close", "ordered_list_close"): self.lists.pop()
            elif kind == "list_item_open":
                active = self.lists[-1]
                self.pending_bullet = f'{active["count"]}.' if active["ordered"] else "•"
                active["count"] += 1
            elif kind == "paragraph_open":
                content = tokens[i + 1]
                marker = re.fullmatch(r"NCBLOCKMATH(\d{3})", content["content"].strip())
                if marker:
                    self.story.append(Paragraph(BLOCKS[int(marker.group(1))], styles["Equation"]))
                else:
                    style = styles["ReportBody"]
                    if self.lists:
                        style = ParagraphStyle("ListItem", parent=style, leftIndent=15, bulletIndent=0)
                    self.story.append(Paragraph(self.inline(content["children"]), style, bulletText=self.pending_bullet))
                    self.pending_bullet = None
                i += 3; continue
            elif kind == "fence":
                if item["content"].lstrip().startswith(("flowchart", "sequenceDiagram")):
                    text = item["content"]
                    kind = "sequence" if "sequenceDiagram" in text else "model" if 'Score at least' in text else "architecture"
                    captions = {"architecture": "System architecture. Offline training supplies trusted artifacts; online inference and transactional persistence have separate responsibilities.",
                                "sequence": "Prediction transaction sequence. Validation/model failures and persistence errors return sanitized failures; delivery can fail after commit.",
                                "model": "Inference workflow. Saved normalization, actual network dimensions and the reviewed threshold produce a survey label, not a diagnosis."}
                    self.story.append(KeepTogether([Diagram(kind), Paragraph(captions[kind], styles["Caption"])]))
                else:
                    text = "<br/>".join(esc(line).replace(" ", "&#160;") for line in item["content"].rstrip().splitlines())
                    # Ordinary spaces allow safe visual wrapping of long reproducibility commands.
                    text = text.replace("&#160;", " ")
                    self.story.append(Paragraph(text, styles["ReportCode"]))
            i += 1


def make_story():
    renderer = Renderer()
    renderer.story.extend([Cover(), PageBreak(), Paragraph("Contents", styles["PartTitle"])])
    toc = TableOfContents()
    toc.levelStyles = [styles["TOC0"], styles["TOC1"]]
    renderer.story.extend([toc, PageBreak(), Paragraph("PART I", styles["Kicker"])])
    renderer.render("project-report.md", ("Academic project report", "part-report"))
    renderer.story.extend([PageBreak(), Paragraph("APPENDIX A", styles["Kicker"])])
    renderer.render("architecture.md", ("System architecture and workflow", "appendix-architecture"))
    renderer.story.extend([PageBreak(), Paragraph("APPENDIX B", styles["Kicker"])])
    renderer.render("technology-and-algorithm-reference.md", ("Technology and algorithm quick reference", "appendix-reference"))
    return renderer.story


total = len(PdfReader(OUTPUT).pages) if OUTPUT.exists() else 1
for _ in range(3):
    doc = Document(OUTPUT)
    doc.multiBuild(make_story(), canvasmaker=lambda *args, **kwargs: NumberedCanvas(*args, total_pages=total, **kwargs))
    measured = len(PdfReader(OUTPUT).pages)
    if measured == total: break
    total = measured
else:
    raise ValueError("Pagination did not stabilize")
print(OUTPUT)
