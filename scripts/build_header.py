"""Build desktop and compact profile banners with the shared SVG renderer."""

import math

from profile_svg import ROOT, Svg, palette, shell, symbol


def sculpture(svg, cx, cy, size, dark):
    """A folded orbital ribbon, projected from a parametric Mobius surface."""
    def point(u, v):
        r = 1 + v * math.cos(u / 2)
        x, y, z = r * math.cos(u), r * math.sin(u), v * math.sin(u / 2)
        a, b, c = .88, -.48, -.35
        y, z = y*math.cos(a)-z*math.sin(a), y*math.sin(a)+z*math.cos(a)
        x, z = x*math.cos(b)+z*math.sin(b), -x*math.sin(b)+z*math.cos(b)
        x, y = x*math.cos(c)-y*math.sin(c), x*math.sin(c)+y*math.cos(c)
        return (x, y, z)

    pieces = []
    for i in range(120):
        for j in range(8):
            u, u1 = i*math.tau/120, (i+1)*math.tau/120
            v, v1 = -.36+j*.09, -.36+(j+1)*.09
            pts = [point(u,v), point(u1,v), point(u1,v1), point(u,v1)]
            ab = [pts[1][k]-pts[0][k] for k in range(3)]
            ac = [pts[3][k]-pts[0][k] for k in range(3)]
            normal = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
            norm = math.sqrt(sum(n*n for n in normal))
            lit = abs(sum(n*l for n,l in zip(normal,(-.35,-.6,.72)))/norm)
            shade = round(54 + 195 * lit)
            if not dark:
                shade = round(28 + 164 * lit)
            color = f"#{shade:02x}{shade:02x}{shade:02x}"
            xy = [(cx+p[0]*size, cy+p[1]*size) for p in pts]
            path = "M" + "L".join(f"{x:.2f} {y:.2f}" for x,y in xy) + "Z"
            pieces.append((sum(p[2] for p in pts)/4, path, color))
    for _, path, color in sorted(pieces):
        svg.add(f'<path d="{path}" fill="{color}" stroke="{color}" stroke-width=".45" stroke-linejoin="round"/>')


def render(dark, mobile=False):
    c = palette(dark)
    w, h = (640, 700) if mobile else (1280, 476)
    svg = Svg(w, h, "Muhammad Raihan Surya · astrorehan",
              "IT student at Universitas Gadjah Mada, Indonesia. Web applications, data and machine learning, developer tools.")
    shell(svg, c)
    pad = 36 if mobile else 52
    symbol(svg, pad, 35, 25, c["ink"])
    svg.text("astrorehan", pad+38, 54, 18, c["ink"], "Geist", 500)
    svg.text("PERSONAL SPACE", w-pad, 52, 12, c["muted"], "GeistMono", 400, .08, "right")
    svg.line(pad, 82, w-pad, 82, c["subtle"])

    if mobile:
        sculpture(svg, 478, 175, 83, dark)
        svg.text("Muhammad", pad, 178, 45, c["secondary"], "Geist", 500, -.03)
        svg.text("Raihan", pad, 268, 90, c["ink"], "Geist", 500, -.04)
        svg.text("Surya.", pad, 362, 90, c["ink"], "Geist", 500, -.04)
        svg.text("Building useful things with code,", pad+2, 423, 22, c["secondary"])
        svg.text("data, and a little curiosity.", pad+2, 456, 22, c["secondary"])
        svg.rect(pad, 495, 291, 40, c["raised"], 20)
        svg.text("IT student / UGM / Indonesia", pad+18, 521, 16, c["secondary"], weight=500)
        svg.line(pad, 578, w-pad, 578, c["border"])
        for i, value in enumerate(("Web applications", "Data & ML", "Developer tools")):
            x = pad + i * 195
            svg.text(f"0{i+1}", x, 613, 12, c["muted"], "GeistMono")
            svg.text(value, x, 645, 17, c["secondary"], weight=500)
    else:
        svg.rect(930, 112, 298, 38, c["surface"], 19, c["border"])
        svg.text("IT student / UGM / Indonesia", 1079, 136, 15, c["secondary"], weight=500, align="center")
        sculpture(svg, 1034, 274, 134, dark)
        svg.text("Muhammad", pad, 181, 46, c["secondary"], "Geist", 500, -.03)
        svg.text("Raihan Surya.", pad-2, 285, 96, c["ink"], "Geist", 500, -.04)
        svg.text("Building useful things with code, data, and a little curiosity.", pad+2, 339, 22, c["secondary"])
        svg.line(pad, 382, w-pad, 382, c["border"])
        for i, (value, x) in enumerate((("Web applications",pad),("Data & ML",345),("Developer tools",586))):
            svg.text(f"0{i+1}", x, 423, 12, c["muted"], "GeistMono")
            svg.text(value, x+33, 425, 18, c["secondary"], weight=500)
        svg.text("Curious by default.", w-pad, 425, 16, c["muted"], align="right")
    return svg.finish()


def main():
    for theme in ("dark", "light"):
        for mobile in (False, True):
            suffix = "-mobile" if mobile else ""
            (ROOT / "assets" / f"header-{theme}{suffix}.svg").write_text(render(theme == "dark", mobile), encoding="utf-8", newline="\n")
    print("Built desktop and compact monochrome banners")


if __name__ == "__main__":
    main()
