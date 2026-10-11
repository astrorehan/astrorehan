"""Shared monochrome palette and portable, outlined profile typography."""

from functools import lru_cache
from html import escape
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]


def palette(dark):
    # Neutral surfaces, hairline borders, and type hierarchy adapted from Arc.
    return (
        dict(bg="#101010", surface="#181818", raised="#202020", ink="#f5f5f5",
             secondary="#c1c1c1", muted="#969696", border="#303030", subtle="#242424")
        if dark else
        dict(bg="#ffffff", surface="#f8f8f8", raised="#f0f0f0", ink="#121212",
             secondary="#5b5b5b", muted="#6f6f6f", border="#e2e2e2", subtle="#ededed")
    )


@lru_cache(maxsize=12)
def font(family, weight):
    face = TTFont(ROOT / "fonts" / f"{family}.ttf")
    location = {"wght": weight}
    if family == "Inter":
        location["opsz"] = 14
    return face, face.getGlyphSet(location=location), face.getBestCmap()


class Svg:
    def __init__(self, width, height, title, description):
        self.width, self.height = width, height
        self.title, self.description = title, description
        self.parts, self.glyphs = [], {}

    def add(self, fragment):
        self.parts.append(fragment)

    def rect(self, x, y, width, height, fill, radius=0, stroke=None):
        border = f' stroke="{stroke}" stroke-width="1"' if stroke else ""
        self.add(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"{border}/>')

    def line(self, x1, y1, x2, y2, stroke):
        self.add(f'<path d="M{x1} {y1}H{x2}" stroke="{stroke}"/>' if y1 == y2
                 else f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{stroke}"/>')

    def text(self, value, x, y, size, fill, family="Inter", weight=400, tracking=-.01, align="left"):
        value = str(value)
        face, glyphset, cmap = font(family, weight)
        scale = size / face["head"].unitsPerEm
        offset = 0
        uses = []
        for char in value:
            name = cmap.get(ord(char))
            if name is None:
                raise ValueError(f"Unsupported character {char!r} in {family}")
            glyph = glyphset[name]
            glyph_id = f"g-{family}-{weight}-{ord(char)}"
            if glyph_id not in self.glyphs:
                pen = SVGPathPen(glyphset, ntos=lambda n: f"{n:.2f}".rstrip("0").rstrip("."))
                glyph.draw(pen)
                self.glyphs[glyph_id] = pen.getCommands()
            uses.append(f'<use href="#{glyph_id}" x="{offset:.2f}"/>')
            offset += glyph.width + tracking * face["head"].unitsPerEm
        width = (offset - tracking * face["head"].unitsPerEm) * scale if value else 0
        if align == "right":
            x -= width
        elif align == "center":
            x -= width / 2
        self.add(f'<g fill="{fill}" aria-label="{escape(value, quote=True)}" transform="translate({x:.2f} {y:.2f}) scale({scale:.6f} {-scale:.6f})">{"".join(uses)}</g>')
        return width

    def finish(self):
        glyphs = "".join(f'<path id="{key}" d="{path}"/>' for key, path in self.glyphs.items())
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(self.title)}</title>
<desc id="desc">{escape(self.description)}</desc>
<defs>{glyphs}</defs>
{"\n".join(self.parts)}
</svg>
'''


def shell(svg, colors):
    svg.rect(.5, .5, svg.width-1, svg.height-1, colors["bg"], 34, colors["border"])


def symbol(svg, x, y, size, color):
    # Four softened arcs form the profile mark.
    svg.add(f'<g transform="translate({x} {y}) scale({size/24})" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round"><path d="M2 11C2 6 6 2 11 2M13 2C18 2 22 6 22 11M22 13C22 18 18 22 13 22M11 22C6 22 2 18 2 13"/><path d="M7 12H17M12 7V17"/></g>')
