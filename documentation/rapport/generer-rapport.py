#!/usr/bin/env python3
"""Génère rapport-final.html (schémas SVG + captures légendées) ; le PDF est produit par Chrome headless.

    python documentation/rapport/generer-rapport.py          # HTML seul
    python documentation/rapport/generer-rapport.py --pdf    # HTML + PDF (Chrome headless) + signets (PyMuPDF)
"""
import html
import pathlib
import re

HERE = pathlib.Path(__file__).parent
CAP = "../../docs/devops/captures"


def esc(s):
    return html.escape(s, quote=False)


# --------------------------------------------------------------------------- SVG
BLUE, GREEN, ORANGE, PURPLE, GRAY, RED = "#2563eb", "#16a34a", "#ea580c", "#7c3aed", "#64748b", "#dc2626"
FILL = {BLUE: "#dbeafe", GREEN: "#dcfce7", ORANGE: "#ffedd5", PURPLE: "#ede9fe", GRAY: "#f1f5f9", RED: "#fee2e2"}

DEFS = """<defs>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#475569"/></marker>
<marker id="ahg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#16a34a"/></marker>
<marker id="aho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#ea580c"/></marker>
</defs>"""


def box(x, y, w, h, lines, color=BLUE, fs=13, dash=False, fill=None, tc="#0f172a", rx=10):
    lh = fs + 3
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * lh / 2 + fs * 0.35
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill or FILL[color]}" '
           f'stroke="{color}" stroke-width="2"' + (' stroke-dasharray="6 4"' if dash else "") + "/>")
    for i, line in enumerate(lines):
        size = fs if i == 0 else fs - 2
        weight = "700" if i == 0 else "400"
        out += (f'<text x="{x + w / 2}" y="{y0 + i * lh}" text-anchor="middle" font-size="{size}" '
                f'font-weight="{weight}" fill="{tc}">{esc(line)}</text>')
    return out


def arrow(x1, y1, x2, y2, color="#475569", dash=False, mk="ah", sw=2.5):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" '
            f'marker-end="url(#{mk})"' + (' stroke-dasharray="6 4"' if dash else "") + "/>")


def parrow(d, color="#475569", dash=False, mk="ah", sw=2.5):
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" marker-end="url(#{mk})"'
            + (' stroke-dasharray="6 4"' if dash else "") + "/>")


def txt(x, y, s, fs=12, anchor="middle", fill="#334155", weight="400", italic=False, mono=False):
    fam = ' font-family="Consolas, monospace"' if mono else ""
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{fs}" font-weight="{weight}" '
            f'fill="{fill}"{st}{fam}>{esc(s)}</text>')


def zone(x, y, w, h, title, color, tcolor):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{FILL[color]}" fill-opacity="0.55" '
            f'stroke="{color}" stroke-opacity="0.6" stroke-width="1.5"/>'
            + txt(x + 18, y + 26, title, 13, "start", tcolor, "700"))


def svg(w, h, body):
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'font-family="Segoe UI, Arial, sans-serif">{DEFS}{body}</svg>')


# --------------------------------------------------------------------------- schémas
def d_overview():
    b = zone(20, 20, 960, 160, "JOUR 1  ·  INTÉGRATION CONTINUE  —  Jenkins (poste de développement)", BLUE, "#1d4ed8")
    items = [("GitHub", "branche Dev", GRAY), ("Jenkins", "Poll SCM 5 min", BLUE), ("Tests Jest", "151 tests", GREEN),
             ("SonarQube", "Quality Gate", GREEN), ("Trivy", "0 CRITICAL", ORANGE), ("Docker Hub", "image 1.0.0-sha7", PURPLE)]
    for i, (a, c, col) in enumerate(items):
        x = 38 + i * 150
        b += box(x, 75, 138, 80, [a, c], col)
        if i < 5:
            b += arrow(x + 138, 115, x + 150, 115)
    b += zone(20, 230, 960, 230, "JOUR 2  ·  LIVRAISON CONTINUE  —  GitLab CI/CD + serveur Ubuntu (VMware)", GREEN, "#15803d")
    b += box(38, 302, 150, 76, ["GitLab CI", "validate-tag"], GREEN)
    b += box(228, 302, 150, 76, ["Approbation", "manuelle  ▶"], ORANGE)
    b += arrow(188, 340, 226, 340) + arrow(378, 340, 430, 340, ORANGE, mk="aho")
    b += (f'<rect x="418" y="272" width="548" height="112" rx="12" fill="#ffffff" fill-opacity="0.6" stroke="{GREEN}" '
          f'stroke-width="2" stroke-dasharray="6 4"/>' + txt(432, 292, "VM Ubuntu 22.04", 12, "start", "#15803d", "700"))
    b += box(432, 305, 150, 66, ["GitLab Runner", "executor shell"], GREEN, 12)
    b += box(602, 305, 170, 66, ["Docker Compose", "backend + PostgreSQL"], BLUE, 12)
    b += box(792, 305, 160, 66, ["API :4000", "/v1/health · /v1/ready"], GREEN, 12)
    b += arrow(582, 338, 600, 338) + arrow(772, 338, 790, 338)
    b += box(520, 410, 170, 44, ["Terraform", "contrôle + inventaire"], PURPLE, 12)
    b += box(720, 410, 170, 44, ["Ansible", "Docker · Compose · ufw"], PURPLE, 12)
    b += arrow(605, 410, 605, 386, PURPLE, True) + arrow(805, 410, 805, 386, PURPLE, True)
    b += parrow("M857 155 L857 212 L687 212 L687 302", "#7c3aed", False)
    b += txt(772, 204, "docker pull  (l'image n'est jamais reconstruite)", 12, "middle", "#6d28d9", "600")
    return svg(1000, 470, b)


def d_jenkins():
    stages = [("Checkout", "2 s", GRAY, ""), ("Install", "47 s", GRAY, ""), ("Prisma", "1 s", GRAY, ""),
              ("Tests", "15 s", GREEN, "bloque si test rouge"), ("Docs API", "3 s", PURPLE, ""),
              ("SonarQube", "53 s", GREEN, ""), ("Quality Gate", "10 s", GREEN, "bloque si ≠ PASSED"),
              ("Build image", "18 s", BLUE, ""), ("Scan Trivy", "9 s", ORANGE, "bloque si CRITICAL"),
              ("Push Docker Hub", "66 s", BLUE, "seulement si tout est vert")]
    b = ""
    for i, (n, d, col, note) in enumerate(stages):
        x = 20 + i * 97
        b += f'<circle cx="{x + 43}" cy="40" r="13" fill="{col}"/>' + txt(x + 43, 45, str(i + 1), 13, "middle", "#fff", "700")
        lines = n.split(" ", 1) if len(n) > 9 else [n]
        b += box(x, 62, 86, 70, lines, col, 12)
        b += txt(x + 43, 152, d, 13, "middle", "#0f172a", "700")
        if note:
            words = note.split(" ")
            half = (len(words) + 1) // 2
            for j, ln in enumerate([" ".join(words[:half]), " ".join(words[half:])]):
                b += txt(x + 43, 172 + j * 13, ln, 10, "middle", "#c2410c", "600")
        if i < 9:
            b += arrow(x + 86, 97, x + 97, 97, sw=2)
    for k, (lab, col) in enumerate([("préparation", GRAY), ("qualité", GREEN), ("documentation", PURPLE),
                                    ("packaging", BLUE), ("sécurité", ORANGE)]):
        x = 150 + k * 150
        b += f'<rect x="{x}" y="212" width="16" height="16" rx="3" fill="{col}"/>' + txt(x + 24, 225, lab, 12, "start")
    b += txt(500, 252, "Build de référence #9 : 3 min 54 s au total  (le stage Docs API a été ajouté au build #10)", 12, "middle", "#475569", "400", True)
    return svg(1000, 262, b)


def d_trace():
    nodes = [("Commit", "723d0f4", "GitHub · 10/11 10:14", GRAY), ("Build Jenkins", "#11  ✓ vert", "151 tests · Q.Gate Passed", BLUE),
             ("Tag Docker Hub", "1.0.0-723d0f4", "version + sha court", PURPLE), ("Digest publié", "sha256:0b9848d0…", "par Jenkins (push)", GREEN),
             ("Conteneur en prod", "sha256:0b9848d0…", "lu par docker inspect", GREEN)]
    b = ""
    for i, (a, v, c, col) in enumerate(nodes):
        x = 20 + i * 196
        b += box(x, 40, 170, 96, [a, v, c], col, 13)
        if i < 4:
            b += arrow(x + 170, 88, x + 196, 88)
    b += (f'<rect x="608" y="160" width="366" height="52" rx="10" fill="#dcfce7" stroke="{GREEN}" stroke-width="2"/>'
          + txt(791, 183, "✓  même digest à l'octet près", 14, "middle", "#166534", "700")
          + txt(791, 202, "l'artefact testé est l'artefact déployé", 12, "middle", "#166534"))
    b += txt(20, 190, "Chaque maillon est consultable : GitHub, console Jenkins, Docker Hub, VM.", 12, "start", "#475569", "400", True)
    return svg(1000, 232, b)


def d_gitlab():
    b = box(40, 70, 220, 84, ["validate-tag", "automatique"], GREEN, 14)
    b += box(340, 70, 220, 84, ["deploy-production", "approbation manuelle"], ORANGE, 14)
    b += box(640, 70, 220, 84, ["smoke-test", "automatique"], GREEN, 14)
    b += box(880, 82, 100, 60, ["API", "en ligne"], BLUE, 13)
    b += arrow(260, 112, 338, 112) + arrow(560, 112, 638, 112) + arrow(860, 112, 878, 112)
    b += txt(299, 100, "tag valide ✓", 11, "middle", "#166534") + txt(599, 100, "après le clic ▶", 11, "middle", "#c2410c")
    b += (f'<circle cx="450" cy="30" r="9" fill="{ORANGE}"/><path d="M432 52 Q450 36 468 52 L468 56 L432 56z" fill="{ORANGE}"/>'
          + txt(502, 40, "vous : qui · quand · quelle version", 11, "start", "#c2410c", "600"))
    b += box(340, 200, 220, 56, ["rollback-production", "manuel · PREVIOUS_TAG"], ORANGE, 13, True)
    b += parrow("M750 154 L750 228 L562 228", ORANGE, True, "aho")
    b += txt(655, 245, "en cas de problème", 11, "middle", "#c2410c", "400", True)
    b += txt(40, 205, "Runner installé sur la VM", 12, "start", "#475569", "600")
    b += txt(40, 223, "tag souverainrecrut-vm", 12, "start", "#475569")
    b += txt(40, 247, "6 variables, dont 2 masquées", 12, "start", "#475569", "600")
    b += txt(40, 265, "clé SSH en type File", 12, "start", "#475569")
    return svg(1000, 285, b)


def d_infra():
    b = zone(15, 25, 280, 340, "Poste de développement (Windows)", BLUE, "#1d4ed8")
    b += box(30, 80, 240, 46, ["SonarQube", "conteneur Docker"], GREEN, 12)
    b += box(30, 150, 240, 50, ["Jenkins", "conteneur Docker"], BLUE, 12)
    b += box(30, 225, 240, 46, ["Ansible", "conteneur éphémère"], PURPLE, 12)
    b += box(30, 290, 240, 46, ["Terraform", "conteneur éphémère"], PURPLE, 12)
    b += zone(355, 25, 290, 320, "Internet (services en ligne)", GRAY, "#334155")
    b += box(375, 70, 250, 50, ["GitLab", "souverainrecrut-deploy"], ORANGE, 12)
    b += box(375, 150, 250, 50, ["GitHub", "souverainrecrut · branche Dev"], GRAY, 12)
    b += box(375, 230, 250, 50, ["Docker Hub", "aarontiavin/souverainrecrut-backend"], PURPLE, 12)
    b += zone(685, 25, 300, 420, "VM Ubuntu 22.04 (VMware)", GREEN, "#15803d")
    b += box(715, 70, 240, 50, ["GitLab Runner", "shell · tag souverainrecrut-vm"], GREEN, 12)
    b += (f'<rect x="700" y="140" width="270" height="170" rx="12" fill="#fff" fill-opacity="0.6" stroke="{BLUE}" stroke-width="2" stroke-dasharray="6 4"/>'
          + txt(714, 160, "Docker Engine 29.9 + Compose", 12, "start", "#1d4ed8", "700"))
    b += box(715, 172, 240, 52, ["backend  (API :4000)", "image Docker Hub"], BLUE, 12)
    b += box(715, 238, 240, 56, ["PostgreSQL 16", "volume postgres_data"], BLUE, 12)
    b += box(715, 330, 240, 40, ["ufw : 22 et 4000 seulement"], GRAY, 12)
    b += arrow(270, 175, 373, 175) + txt(322, 167, "Poll SCM", 11)
    b += arrow(270, 190, 373, 252) + txt(300, 232, "push", 11, "start")
    b += arrow(625, 255, 713, 205, "#7c3aed") + txt(664, 252, "docker pull", 11, "middle", "#6d28d9", "600")
    b += arrow(713, 95, 627, 95) + txt(670, 86, "récupère les jobs", 11)
    b += parrow("M270 248 L305 248 L305 405 L683 405", PURPLE, True)
    b += (f'<line x1="270" y1="313" x2="305" y2="313" stroke="{PURPLE}" stroke-width="2.5" stroke-dasharray="6 4"/>'
          + txt(450, 398, "SSH · clé dédiée ed25519", 12, "middle", "#6d28d9", "600"))
    return svg(1000, 460, b)


def d_rollback():
    b = ""
    states = [(150, "①", "Déploiement initial", "1.0.0-723d0f4", BLUE), (500, "②", "Rollback", "1.0.0-12a585b", ORANGE),
              (850, "③", "Retour en avant", "1.0.0-723d0f4", BLUE)]
    for cx, n, t, tag, col in states:
        b += f'<circle cx="{cx}" cy="90" r="46" fill="{FILL[col]}" stroke="{col}" stroke-width="3"/>' + txt(cx, 102, n, 34, "middle", col, "700")
        b += txt(cx, 168, t, 14, "middle", "#0f172a", "700") + txt(cx, 188, tag, 13, "middle", "#334155", "400", False, True)
        b += txt(cx, 207, "/v1/ready : READY ✓  · 1 candidat", 11, "middle", "#166534", "600")
    b += arrow(200, 90, 448, 90, ORANGE, mk="aho") + txt(324, 76, "./rollback.sh 1.0.0-12a585b", 12, "middle", "#c2410c", "600", False, True)
    b += arrow(552, 90, 798, 90, BLUE) + txt(675, 76, "./rollback.sh 1.0.0-723d0f4", 12, "middle", "#1d4ed8", "600", False, True)
    b += (f'<rect x="60" y="236" width="880" height="44" rx="10" fill="#fef9c3" stroke="#ca8a04" stroke-width="2"/>'
          + txt(500, 263, "PostgreSQL · volume souverainrecrut_postgres_data : les données traversent les trois versions", 13, "middle", "#713f12", "700"))
    return svg(1000, 296, b)


def d_progress():
    cols = [("1 · MANUEL", "Comprendre", GRAY, ["Jour 1 : npm test, sonar-scanner,", "docker build lancés à la main", "Jour 2 : ssh, docker run à la main"]),
            ("2 · SCRIPTÉ", "Reproduire", BLUE, ["Jour 1 : build + push en script", "Jour 2 : deploy.sh, rollback.sh,", "playbook Ansible, Terraform"]),
            ("3 · AUTOMATISÉ", "Industrialiser", GREEN, ["Jour 1 : Jenkinsfile, à chaque commit", "Jour 2 : pipeline GitLab,", "approbation manuelle tracée"])]
    b = ""
    for i, (t, s, col, lines) in enumerate(cols):
        x = 20 + i * 330
        b += f'<rect x="{x}" y="20" width="300" height="190" rx="12" fill="{FILL[col]}" stroke="{col}" stroke-width="2"/>'
        b += f'<rect x="{x}" y="20" width="300" height="50" rx="12" fill="{col}"/><rect x="{x}" y="50" width="300" height="20" fill="{col}"/>'
        b += txt(x + 150, 42, t, 15, "middle", "#fff", "700") + txt(x + 150, 61, s, 12, "middle", "#fff")
        for j, ln in enumerate(lines):
            b += txt(x + 16, 108 + j * 26, ln, 12.5, "start", "#0f172a")
        if i < 2:
            b += arrow(x + 302, 115, x + 328, 115, sw=3)
    return svg(1000, 230, b)


def d_vocab():
    b = box(20, 66, 120, 60, ["Commit"], GRAY)
    b += box(170, 66, 230, 60, ["Build · tests · qualité", "scan de sécurité"], BLUE, 13)
    b += box(430, 66, 130, 60, ["Image", "publiée"], PURPLE, 13)
    b += f'<polygon points="590,96 640,56 690,96 640,136" fill="{FILL[ORANGE]}" stroke="{ORANGE}" stroke-width="2.5"/>'
    b += txt(640, 93, "Porte", 12, "middle", "#9a3412", "700") + txt(640, 108, "humaine", 11, "middle", "#9a3412")
    b += box(730, 66, 240, 60, ["Production", "API en ligne"], GREEN, 13)
    b += arrow(140, 96, 168, 96) + arrow(400, 96, 428, 96) + arrow(560, 96, 588, 96) + arrow(690, 96, 728, 96, ORANGE, mk="aho")
    for y, x1, x2, col, lab, dash in [(160, 20, 560, BLUE, "INTÉGRATION CONTINUE  (Jenkins)", False),
                                      (192, 430, 690, GREEN, "LIVRAISON CONTINUE : prêt à déployer, un humain décide", False),
                                      (224, 560, 970, GRAY, "DÉPLOIEMENT CONTINU : pas de porte (non retenu ici)", True)]:
        b += (f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{col}" stroke-width="5" stroke-linecap="round"'
              + (' stroke-dasharray="3 9"' if dash else "") + "/>")
        b += txt(x1, y - 8, lab, 11.5, "start", col if col != GRAY else "#475569", "700")
    return svg(1000, 245, b)


def d_migration():
    rows = [("Avant optimisation", 280, RED, "4 min 40 s"), ("1er passage (remplit le cache)", 53, ORANGE, "53 s"), ("Passages suivants (cache npm)", 13, GREEN, "13 s")]
    b = ""
    for i, (lab, v, col, t) in enumerate(rows):
        y = 24 + i * 52
        w = v * 2.3
        b += txt(250, y + 22, lab, 13, "end", "#0f172a") + f'<rect x="262" y="{y}" width="{w}" height="34" rx="5" fill="{col}"/>'
        b += txt(262 + w + 10, y + 23, t, 14, "start", col, "700")
    return svg(1000, 180, b)


def d_builds():
    data = [(5, 430, 0), (6, 212, 0), (7, 396, 0), (8, 282, 0), (9, 234, 1), (10, 314, 1), (11, 154, 1), (12, 97, 1), (13, 70, 1), (14, 98, 1)]
    b = '<line x1="40" y1="250" x2="980" y2="250" stroke="#94a3b8" stroke-width="2"/>'
    for i, (n, d, ok) in enumerate(data):
        x = 70 + i * 90
        h = d * 0.44
        col = GREEN if ok else RED
        b += f'<rect x="{x}" y="{250 - h}" width="60" height="{h}" rx="5" fill="{col}"/>'
        b += txt(x + 30, 250 - h - 8, f"{d} s", 13, "middle", col, "700") + txt(x + 30, 272, f"#{n}", 13, "middle", "#0f172a", "700")
    for k, (lab, col) in enumerate([("échec", RED), ("succès", GREEN)]):
        b += f'<rect x="{760 + k * 110}" y="14" width="16" height="16" rx="3" fill="{col}"/>' + txt(784 + k * 110, 27, lab, 12, "start")
    b += txt(40, 24, "Durée d'un build Jenkins (secondes)", 12, "start", "#475569", "600")
    return svg(1000, 290, b)


def d_deploy():
    steps = [["① Mémoriser", "le tag en cours", "(.previous_tag)"], ["② docker pull", "de l'image taguée", "jamais de build"],
             ["③ Extraire prisma/", "de l'image", "bonnes migrations"], ["④ migrate deploy", "conteneur éphémère", "cache npm : 13 s"],
             ["⑤ Démarrer l'API", "attendre /v1/ready", "READY sous 60 s"]]
    b = ""
    for i, s in enumerate(steps):
        x = 20 + i * 195
        b += box(x, 30, 170, 84, s, BLUE if i != 3 else GREEN, 13)
        if i < 4:
            b += arrow(x + 170, 72, x + 195, 72)
    b += txt(500, 150, "Si l'API n'est pas READY après 60 s : affichage des logs et code de sortie non nul (le pipeline passe en rouge).", 12, "middle", "#475569", "400", True)
    return svg(1000, 168, b)


# --------------------------------------------------------------------------- éléments de page
FIGS = []  # (id, numéro, légende)
PARTS = []


def reg(fid, cap):
    FIGS.append((fid, len(FIGS) + 1, cap))
    return len(FIGS)


def R(fid):
    return f"§§{fid}§§"


def add(s):
    PARTS.append(s)


def fig(fid, src, cap):
    n = reg(fid, cap)
    add(f'<figure id="fig-{fid}"><img src="{CAP}/{src}" alt=""><figcaption><b>Figure {n}</b> — {cap}</figcaption></figure>')


def dia(fid, svgstr, cap):
    n = reg(fid, cap)
    add(f'<figure class="dia" id="fig-{fid}">{svgstr}<figcaption><b>Figure {n}</b> — {cap}</figcaption></figure>')


def term(fid, title, text, cap):
    n = reg(fid, cap)
    add(f'<figure class="termfig" id="fig-{fid}"><div class="term"><div class="termbar"><i></i><i></i><i></i><span>{esc(title)}</span></div>'
        f'<pre>{esc(text.strip(chr(10)))}</pre></div><figcaption><b>Figure {n}</b> — {cap}</figcaption></figure>')


def h1(num, title, anchor):
    add(f'<h1 id="{anchor}"><span>{num}</span>{title}</h1>')


def h2(title):
    add(f"<h2>{title}</h2>")


def p(s):
    add(f"<p>{s}</p>")


def note(kind, s):
    add(f'<div class="note {kind}">{s}</div>')


def table(head, rows, cls=""):
    t = f'<table class="{cls}"><thead><tr>' + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead><tbody>"
    for r in rows:
        t += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    add(t + "</tbody></table>")


OK, WARN, KO = "✅", "⚠️", "❌"

# ============================================================================ CONTENU
add(f"""<section class="cover">
<div class="cover-top">Mastère Expert en Développement et Déploiement de Solutions Numériques Sécurisées · RNCP 40166</div>
<div class="cover-mid">
<div class="cover-kicker">Projet fil rouge CI/CD · Module de 14 h · Blocs 4 et 5</div>
<h1 class="cover-title">SouverainRecrut<br>du commit à la production</h1>
<div class="cover-sub">Industrialisation, sécurisation et déploiement d'une API Backend<br>Jenkins · SonarQube · Trivy · Docker · Terraform · Ansible · GitLab CI/CD</div>
<div class="cover-art">{d_vocab()}</div>
</div>
<table class="cover-meta">
<tr><td>Auteurs</td><td><b>Joan Carpentier</b> · <b>Aaron Tiavinjanahary</b></td></tr>
<tr><td>Formateur</td><td>Alimou Diallo — Sup de Vinci Rennes</td></tr>
<tr><td>Dates</td><td>9 et 10 novembre 2026</td></tr>
<tr><td>Dépôt du code</td><td><a>https://github.com/AaronTia/souverainrecrut.git</a> (branche Dev)</td></tr>
<tr><td>Dépôt de déploiement</td><td><a>https://gitlab.com/WakakiVongola/souverainrecrut-deploy.git</a></td></tr>
</table>
</section>""").

add("""<section class="glance">
<h2 class="toc-title">En un coup d'œil</h2>
<p class="lead"><b>SouverainRecrut</b> est une API de gestion de recrutement. Chaque modification du code est testée, analysée,
packagée puis déployée sur un serveur. Une personne approuve la mise en production, et tout peut revenir en arrière en quelques minutes.</p>
<table class="glance-t">
<tr><th>Vous cherchez…</th><th>La réponse</th><th>Où la trouver</th></tr>
<tr><td>L'application tourne-t-elle ?</td><td>Oui : API en ligne, base connectée, pipeline GitLab vert.</td><td>§§gl-pipe§§ · §§term-verif§§</td></tr>
<tr><td>Le code est-il de qualité ?</td><td>151 tests, 99,4 % de couverture, Quality Gate « Passed ».</td><td>§ 4.2 · §§cap-sonar§§</td></tr>
<tr><td>Est-ce sécurisé ?</td><td>Scan d'image : 0 vulnérabilité critique ; secrets hors dépôt ; mise en production approuvée.</td><td>§ 4.3 · § 9</td></tr>
<tr><td>Ce qui est déployé est-il ce qui a été testé ?</td><td>Oui : même empreinte (digest) de Jenkins à la production.</td><td>§ 8 · §§trace§§</td></tr>
<tr><td>Peut-on revenir en arrière ?</td><td>Oui, testé sur trois versions, données conservées.</td><td>§ 7.2 · §§rollback§§</td></tr>
<tr><td>Comment déployer ?</td><td>Terraform contrôle le serveur, Ansible le configure, GitLab déploie après approbation.</td><td>§ 5 et § 6 · <code>deploiement/README.md</code></td></tr>
<tr><td>Ce qui manque ou reste limité ?</td><td>SBOM, signature d'image, tests de charge, environnement de préproduction.</td><td>§ 14</td></tr>
<tr><td>Qui a réalisé le projet ?</td><td>Joan Carpentier et Aaron Tiavinjanahary.</td><td>page de garde</td></tr>
</table>
<div class="retenir"><b>À retenir</b>
<ol><li>L'image testée est exactement celle qui tourne en production (même empreinte, vérifiée aux deux extrémités).</li>
<li>La mise en production exige une approbation humaine, tracée par GitLab (qui, quand, quelle version).</li>
<li>Les limites sont assumées et documentées : base de données simulée dans les tests, Ubuntu 22.04, pas de HTTPS.</li></ol></div>
</section>""")

add("""<section class="toc"><h2 class="toc-title">Sommaire</h2><ol>
<li><a href="#s1">Résumé exécutif</a><span>l'essentiel en une page</span></li>
<li><a href="#s2">Contexte, objectifs et démarche</a><span>CI/CD, du manuel à l'automatique</span></li>
<li><a href="#s3">Architecture de la chaîne</a><span>outils, flux, deux dépôts</span></li>
<li><a href="#s4">Jour 1 · Intégration continue</a><span>Jenkins, tests, Sonar, Trivy, Docker Hub</span></li>
<li><a href="#s5">Jour 2 · Serveur et déploiement</a><span>Terraform, Ansible, Docker Compose</span></li>
<li><a href="#s6">Pipeline GitLab CI/CD</a><span>runner, variables, approbation manuelle</span></li>
<li><a href="#s7">Vérification et rollback</a><span>scénario testé sur trois versions</span></li>
<li><a href="#s8">Traçabilité du commit à la production</a><span>le digest, preuve de bout en bout</span></li>
<li><a href="#s9">Sécurité de la livraison</a><span>secrets, incident de la clé</span></li>
<li><a href="#s10">Qualité du code de référence</a><span>défauts identifiés par les tests</span></li>
<li><a href="#s11">Performances et incidents</a><span>rétrospective chiffrée</span></li>
<li><a href="#s12">Indicateurs DORA et Definition of Done</a><span>piloter la livraison</span></li>
<li><a href="#s13">Argumentaire MSPR 4.1 et 5.1</a><span>valeur ajoutée, fiabilité, réversibilité</span></li>
<li><a href="#s14">Écarts, limites et perspectives</a><span>ce qui n'est pas fait, et pourquoi</span></li>
<li><a href="#annexes">Annexes</a><span>livrable, reproduction, glossaire, figures</span></li>
</ol></section>""")

# ------------------------------------------------------------------ 1. Résumé
h1("1", "Résumé exécutif", "s1")
p("<b>SouverainRecrut</b> est une application de gestion de recrutement. Ce rapport décrit la chaîne qui mène, sans autre "
  "intervention humaine qu'une approbation, d'un <b>commit sur GitHub</b> à une <b>API en ligne sur un serveur Ubuntu</b>, "
  "avec tests, analyse qualité, scan de sécurité, image versionnée, déploiement et retour arrière. Périmètre : le backend uniquement.")
add("""<div class="kpis">
<div class="kpi"><b>151</b><span>tests automatisés<br>99,4 % de couverture</span></div>
<div class="kpi g"><b>0</b><span>vulnérabilité CRITICAL<br>dans l'image publiée</span></div>
<div class="kpi"><b>6 / 6</b><span>builds Jenkins verts<br>depuis la stabilisation</span></div>
<div class="kpi o"><b>13 s</b><span>migration de base<br>(4 min 40 s avant)</span></div>
<div class="kpi g"><b>≈ 3 min</b><span>pour revenir à<br>la version précédente</span></div>
<div class="kpi"><b>19 / 19</b><span>livrables du Jour 2<br>réalisés et prouvés</span></div>
</div>""")
h2("État des exigences du cahier des charges")
table(["Exigence", "Résultat", "Preuve"], [
    ["Tests backend + rapport de couverture exploitable", f"{OK} 151 tests, 99,4 % des lignes", f"{R('cap-tests')}, {R('cap-cov')}"],
    ["SonarQube et Quality Gate PASSED", f"{OK} Passed, 0 duplication", f"{R('cap-sonar')}"],
    ["Jenkinsfile : checkout → tests → Sonar → image → Trivy → push", f"{OK} builds #9 à #14 verts", f"{R('jenkins-stages')}, {R('cap-jenkins-hist')}"],
    ["Image Docker taguée, scannée et publiée", f"{OK} <code>1.0.0-723d0f4</code>", f"{R('cap-trivy')}, {R('cap-dh-tags')}"],
    ["VM Ubuntu configurée par Ansible", f"{OK} Docker, Compose, pare-feu, runner", f"{R('term-ans')}"],
    ["Terraform", f"{OK} avec adaptation (pas d'ESXi)", f"{R('term-tf')}"],
    ["Déploiement Compose + PostgreSQL depuis Docker Hub", f"{OK} API joignable, données persistantes", f"{R('term-verif')}"],
    ["Pipeline GitLab avec approbation manuelle", f"{OK} validate → deploy (approuvé) → smoke-test", f"{R('gl-pipe')}, {R('gl-env')}"],
    ["Rollback documenté et testé", f"{OK} 723d0f4 → 12a585b → 723d0f4", f"{R('rollback')}, {R('term-rollback')}"],
    ["Traçabilité et reproductibilité", f"{OK} digest identique Jenkins ↔ production", f"{R('trace')}"],
    ["Options du cours : SBOM, signature d'image", f"{KO} non réalisées", "§ 14"],
])
note("ok", "<b>Message clé.</b> L'image testée par Jenkins est <b>exactement</b> celle qui tourne en production : son digest "
           f"<code>sha256:0b9848d0…</code> est identique aux deux extrémités ({R('trace')}). Le déploiement est approuvé "
           "par un humain, tracé par GitLab, et réversible en quelques minutes.")

# ------------------------------------------------------------------ 2. Contexte
h1("2", "Contexte, objectifs et démarche", "s2")
note("", "<b>En bref.</b> Pourquoi cette chaîne, et la progression suivie : manuel, puis scripté, puis automatisé.")
p("Le cahier des charges demande une chaîne <b>automatisée, reproductible, sécurisée, traçable et documentée</b>, "
  "et pas seulement une API qui fonctionne. Le tableau ci-dessous relie chaque exigence qualité (cahier § 7) à ce qui a été réalisé.")
table(["Exigence", "Ce qui a été fait", "Où le vérifier"], [
    ["Reproductibilité", "Tout est en code : Jenkinsfile, Dockerfile, Ansible, Terraform, Compose, <code>.gitlab-ci.yml</code>", "Annexe B"],
    ["Qualité logicielle", "Jest, couverture, SonarQube avec Quality Gate bloquant", "§ 4.2"],
    ["Sécurité", "Scan Trivy bloquant, image non-root, secrets hors dépôt, pare-feu", "§ 4.3, § 9"],
    ["Traçabilité", "Tag <code>version-sha</code> relié au commit, digest vérifié en production", "§ 8"],
    ["Déploiement", "Le serveur tire l'image publiée ; elle n'est jamais reconstruite", "§ 5, § 6"],
    ["Continuité", "Rollback testé, limites sur les migrations documentées", "§ 7"],
    ["Documentation", "README du pipeline, runbook de 11 incidents, procédures, ce rapport", "Annexe A"],
])
h2("Vocabulaire : CI, livraison continue, déploiement continu")
p("Le cours distingue trois notions. La chaîne réalisée est en <b>livraison continue</b> : l'artefact est toujours prêt à être déployé, "
  "et une <b>porte humaine</b> (l'approbation manuelle exigée par le cahier) précède la production.")
dia("vocab", d_vocab(), "Où se situent l'intégration continue, la livraison continue et le déploiement continu dans la chaîne du projet.")
h2("Démarche : du manuel à l'automatique")
p("La progression suivie reprend celle du cours : comprendre en manuel, reproduire par script, puis industrialiser par un pipeline. "
  "Chaque étape a été exécutée à la main avant d'être automatisée, ce qui a permis de repérer les pannes tôt.")
dia("progress", d_progress(), "Progression suivie sur les deux jours : manuel, scripté, automatisé.")

# ------------------------------------------------------------------ 3. Architecture
h1("3", "Architecture de la chaîne", "s3")
note("", "<b>En bref.</b> Deux parties : le Jour 1 produit une image testée, le Jour 2 la déploie. Le tag de l'image les relie.")
p("La chaîne est en deux parties. Le <b>Jour 1</b> produit une image fiable ; le <b>Jour 2</b> la déploie sur un serveur. "
  "Le seul lien entre les deux est le <b>tag de l'image</b>, validé avant tout déploiement.")
dia("overview", d_overview(), "Vue d'ensemble : intégration continue (haut) et livraison continue (bas), reliées par l'image Docker Hub.")
dia("infra", d_infra(), "Répartition physique : le poste de développement, les services en ligne et la machine virtuelle de déploiement.")
h2("Rôle de chaque outil")
table(["Outil", "Rôle", "Pourquoi ce choix"], [
    ["GitHub", "Dépôt du code (fork, branche <code>Dev</code>)", "imposé par le cahier ; scruté par Jenkins"],
    ["Jenkins", "Orchestre build, tests, qualité, image, scan, publication", "<i>pipeline as code</i> (<code>Jenkinsfile</code>)"],
    ["SonarQube", "Analyse statique et Quality Gate", "barrière automatique avant tout artefact"],
    ["Trivy", "Scan des vulnérabilités de l'image", "bloque la publication d'une image dangereuse"],
    ["Docker Hub", "Registre : image <code>version-sha7</code>", "l'artefact testé est celui déployé"],
    ["Terraform", "Contrôle du serveur, génération de l'inventaire", "infrastructure décrite en code, rejouable"],
    ["Ansible", "Installe Docker, Compose, pare-feu, runner", "idempotent, sans agent"],
    ["GitLab CI/CD", "Déploie, approbation manuelle, rollback", "imposé par le cahier ; projet séparé du code"],
    ["Docker Compose", "Orchestre backend et PostgreSQL", "volume persistant, healthchecks, redémarrage auto"],
])
note("", "<b>Deux dépôts, volontairement.</b> GitHub contient le code et produit l'image ; GitLab ne contient que les fichiers de "
         "déploiement et la consomme. C'est le motif <i>multi-dépôts</i> vu au cours : le pipeline du backend produit, "
         "le pipeline d'infrastructure déploie.")

# ------------------------------------------------------------------ 4. Jour 1
h1("4", "Jour 1 · Intégration continue", "s4")
note("", "<b>En bref.</b> Un pipeline Jenkins en dix étapes, avec quatre portes de contrôle. Les scans ont bloqué deux publications avant qu'elles ne passent.")
h2("4.1  Le pipeline Jenkins")
p("Le <code>Jenkinsfile</code> versionné avec le code définit <b>dix étapes</b>. Quatre d'entre elles sont des <b>portes</b> : "
  "si l'une échoue, la suite n'est pas exécutée et <u>aucune image n'est publiée</u>. Jenkins interroge GitHub toutes les 5 minutes "
  "(<i>Poll SCM</i>) car il tourne en local et GitHub ne peut pas le joindre par webhook.")
dia("jenkins-stages", d_jenkins(), "Les dix étapes du pipeline Jenkins, leur durée et les quatre portes de contrôle (en orange).")
fig("cap-jenkins-pipe", "02-jenkins-pipeline-overview.jpg", "Vue Pipeline de Jenkins pour le build de référence #9 : toutes les étapes sont vertes, l'image est publiée à la fin.")
fig("cap-jenkins-hist", "19-jenkins-historique-builds.jpg", "Page du job : builds #12 à #14 verts, Quality Gate « Passed », courbe des tests (127 puis 150) et artefacts archivés, dont la documentation de l'API.")

h2("4.2  Tests et qualité du code")
p("La suite de tests contient aujourd'hui <b>18 suites et 151 tests</b> : unitaires, d'intégration HTTP (<code>supertest</code>), "
  "configuration Jest et couverture.")
p("<b>Modifications apportées à la suite.</b> Retrait des tests qui recopiaient l'implémentation (appels Prisma figés) ou ne "
  "vérifiaient qu'un <code>typeof</code>, ajout de tests de sécurité réels (jeton forgé, jeton expiré, algorithme <code>none</code>, "
  "injection de champs), des tests CORS, un test de contrat entre la documentation OpenAPI et les routes, et des tests <code>it.failing</code> "
  "qui documentent les défauts du code de référence (§ 10).")
table(["Mesure", "Valeur", "Seuil exigé par le pipeline"], [
    ["Tests", "151 passés, 18 suites", "tout doit passer"],
    ["Couverture globale (lignes, mesurée par Jest)", "99,4 %", "≥ 90 %"],
    ["Couverture SonarQube (lignes + branches)", "95,8 %", "indicateur, non bloquant"],
    ["Couverture des middlewares et validateurs (sécurité)", "100 %", "100 %"],
    ["SonarQube : duplications / hotspots", "0,0 % / 0", "Quality Gate « Passed »"],
])
fig("cap-tests", "03-jenkins-tests-151-passed.jpg", "Résultats de tests du build #14 publiés par Jenkins (rapport JUnit) : 151 tests passés, aucun échec, aucun test ignoré.")
fig("cap-sonar", "05-sonarqube-quality-gate-passed.jpg", "SonarQube, onglet « New Code » : Quality Gate « Passed », 0 nouveau problème, duplications 0,0 % (seuil 3 %).")
fig("cap-cov", "06-sonarqube-overall-code.jpg", "SonarQube, onglet « Overall Code » : couverture de 95,8 % (SonarQube combine lignes et branches ; Jest mesure 99,4 % des lignes) et 3 problèmes ouverts, tous dans le code de référence et détaillés au § 10 (D7, D8).")
note("warn", "<b>Limite connue.</b> L'accès à la base est simulé (Prisma mocké) : les contraintes d'unicité, les cascades et les clés "
             "étrangères ne sont pas exercées contre PostgreSQL en CI. Les défauts que les tests ont révélés sont listés au § 10.")

h2("4.3  Image Docker et sécurité")
p("Le <code>Dockerfile</code> a été durci en réponse au scan Trivy, qui a <b>bloqué deux publications</b> avant d'être satisfait : "
  "une dépendance d'Express (<code>proxy-addr</code>) et le module <code>tar</code> embarqué dans le <i>npm de l'image de base</i>. "
  "La seconde faille ne venait pas du projet : elle a disparu en supprimant npm de l'image finale.")
table(["Point", "Avant", "Après"], [
    ["Image de base", "<code>node:20-alpine</code>", "<code>node:22-alpine</code> (version exigée par le projet)"],
    ["Construction", "une seule étape", "multi-stage : outils de build absents de l'image finale"],
    ["Outils embarqués", "npm, npx, yarn, corepack", "supprimés (l'API s'exécute avec <code>node</code> seul)"],
    ["Utilisateur", "root", "<code>node</code> (non privilégié)"],
    ["Dépendances", "développement incluses", "production uniquement (<code>npm ci --omit=dev</code>)"],
    ["Résultat Trivy", "2 CRITICAL → publication bloquée", "0 CRITICAL, 16 HIGH reportées dans le rapport archivé"],
])
fig("cap-trivy", "08-jenkins-trivy-bloquant-0-critical.jpg", "Build #14, commande Trivy <b>bloquante</b> (<code>--severity CRITICAL --ignore-unfixed --exit-code 1</code>) : 0 vulnérabilité sur l'image Alpine et ses dépendances, donc la publication est autorisée.")
note("", "<b>Seuil choisi.</b> Seules les vulnérabilités <i>CRITICAL disposant d'un correctif</i> bloquent la publication ; les HIGH sont tracées "
         "et revues. Bloquer sur des failles sans correctif empêcherait toute livraison sans rien améliorer.")

h2("4.4  Publication, secrets et intégration SonarQube")
p("L'image est publiée avec un tag explicite <code>version-sha7</code> (<i>jamais</i> <code>latest</code>). Les identifiants "
  "(jeton SonarQube, accès Docker Hub) sont des <i>credentials</i> Jenkins : ils n'apparaissent ni dans le dépôt ni dans les logs.")
fig("cap-dh-tags", "15-dockerhub-tag-723d0f4-digest.jpg", "Docker Hub, tag <code>1.0.0-723d0f4</code> (la version en production) : son <i>index digest</i> <code>sha256:0b9848d0…7773a</code> est celui affiché par Jenkins au push et par la VM au déploiement.")
fig("cap-cred", "09-jenkins-credentials-masques.jpg", "Credentials Jenkins : le jeton SonarQube et l'accès Docker Hub, valeurs masquées (<code>aarontiavin/******</code>).")
fig("cap-webhook", "10-sonarqube-webhook-jenkins.jpg", "Webhook SonarQube → Jenkins : il permet au pipeline d'attendre le verdict du Quality Gate (dernière livraison réussie).")

h2("4.5  Documentation de l'API générée par le pipeline")
p("Une étape dédiée exporte la spécification OpenAPI depuis le code puis la rend en HTML avec Redocly. La documentation est donc "
  "<b>toujours synchrone avec l'API publiée</b> ; un test de contrat vérifie aussi que chaque route documentée existe réellement.")
fig("cap-redoc", "11-redocly-api-docs.jpg", "Documentation de l'API générée à chaque build (Redocly) : 14 routes regroupées par domaine fonctionnel.")

# ------------------------------------------------------------------ 5. Jour 2 : serveur
h1("5", "Jour 2 · Serveur et déploiement", "s5")
note("", "<b>En bref.</b> Une machine virtuelle Ubuntu configurée par Ansible, vérifiée par Terraform, et qui fait tourner l'API avec PostgreSQL via Docker Compose.")
h2("5.1  La machine virtuelle")
table(["Caractéristique", "Valeur"], [
    ["Système", "Ubuntu Server 22.04.5 LTS (le cahier indique 24.04 : sans incidence ici)"],
    ["Ressources", "2 vCPU, 3,8 Go de RAM, 29 Go de disque"],
    ["Réseau", "NAT VMware, adresse 192.168.139.128, accès SSH"],
    ["Snapshot", "« post-install », réalisé avant toute configuration"],
    ["Accès", "clé SSH ed25519 dédiée au déploiement, <code>sudo</code> sans mot de passe pour l'automatisation"],
])
h2("5.2  Terraform : décrire et contrôler le serveur")
p("Le fournisseur <code>vsphere</code> exige un ESXi ou un vCenter. Avec <b>VMware Workstation seul</b>, la VM est donc créée à la main "
  "(ce que prévoit le cahier, § 4.2) et Terraform est utilisé sur ce qui est réellement pilotable : il <b>génère l'inventaire Ansible</b> "
  "depuis ses variables et <b>vérifie par SSH</b> que le serveur est prêt (Docker actif, Compose, répertoire de déploiement, espace disque). "
  "Un second <code>plan</code> répond « No changes » : la configuration est idempotente.")
term("term-tf", "terraform apply  (extrait)", """
$ terraform apply
local_file.ansible_inventory: Creation complete after 0s
null_resource.vm_ready_check (remote-exec): Connected!
null_resource.vm_ready_check (remote-exec): OS      : Ubuntu 22.04.5 LTS
null_resource.vm_ready_check (remote-exec): CPU     : 2 vCPU | RAM : 3868 Mo
null_resource.vm_ready_check (remote-exec): Docker version 29.9.3, build 5457199
null_resource.vm_ready_check (remote-exec): Docker Compose version v5.7.0
null_resource.vm_ready_check (remote-exec): active
null_resource.vm_ready_check (remote-exec): Disque libre : 12 Go
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

$ terraform plan        # second passage
No changes. Your infrastructure matches the configuration.
""", "Terraform contrôle le serveur par SSH puis génère l'inventaire ; un second passage ne change rien.")
h2("5.3  Ansible : configurer le serveur")
p("Le <i>playbook</i> installe Docker Engine et le plugin Compose depuis le dépôt officiel, active le service, crée "
  "<code>/opt/souverainrecrut</code>, configure le pare-feu (<b>deny par défaut</b>, ports 22 et 4000 seulement) et installe le "
  "GitLab Runner. Il est <b>idempotent</b> et s'exécute depuis un conteneur Docker (Ansible ne tourne pas nativement sous Windows).")
term("term-ans", "ansible-playbook  (extraits)", """
TASK [Installer Docker Engine et le plugin Compose] ***  changed
TASK [Autoriser SSH et l'API dans le pare-feu] ********  changed  (22, 4000)
TASK [Installer GitLab Runner] ************************  changed
TASK [Afficher les versions installées] ***************
    "Docker version 29.9.3, build 5457199",
    "Docker Compose version v5.7.0"

PLAY RECAP *********************************************
192.168.139.128 : ok=8  changed=4  unreachable=0  failed=0  skipped=0
""", "Ansible : serveur prêt (Docker 29.9.3, Compose v5.7.0), sans aucun échec au dernier passage.")
h2("5.4  Docker Compose et script de déploiement")
table(["Service", "Image", "Particularités"], [
    ["<code>backend</code>", "<code class=\"dg\">aarontiavin/souverainrecrut-backend:&lt;tag&gt;</code>", "tirée de Docker Hub, healthcheck sur <code>/v1/ready</code>, redémarrage automatique"],
    ["<code>db</code>", "<code>postgres:16-alpine</code>", "volume persistant, non publié sur l'hôte, healthcheck <code>pg_isready</code>"],
    ["<code>migrate</code>", "<code>node:22-alpine</code>", "éphémère ; applique les migrations Prisma ; cache npm persistant"],
])
dia("deploy-flow", d_deploy(), "Les cinq étapes du script <code>deploy.sh</code>, appelé aussi par le pipeline GitLab.")
p("Les migrations sont <b>extraites de l'image déployée</b> (et non d'un autre dépôt) : une version applique toujours ses propres migrations. "
  "La CLI Prisma n'est pas embarquée dans l'image de production ; elle est téléchargée une seule fois puis conservée dans un volume (13 s ensuite).")
term("term-deploy", "deploy.sh  (log du job GitLab, extrait)", """
==> Pull aarontiavin/souverainrecrut-backend:1.0.0-723d0f4
Digest: sha256:0b9848d00e9d21685eb0419dc9ccfe2a29a06fa18a26f0b86f7f034ed4e7773a
Status: Image is up to date for aarontiavin/souverainrecrut-backend:1.0.0-723d0f4
==> Extraction des migrations Prisma de l'image
20260630124434_init
==> Base de données
 Container souverainrecrut-db Healthy
1 migration found in prisma/migrations
No pending migrations to apply.
==> Backend
==> Vérification
""", "Journal du déploiement : l'image est tirée (digest affiché), les migrations vérifiées, puis l'API démarrée.")

# ------------------------------------------------------------------ 6. GitLab
h1("6", "Pipeline GitLab CI/CD", "s6")
note("", "<b>En bref.</b> Le pipeline GitLab tourne sur le runner installé sur la VM. La mise en production attend un clic humain.")
h2("6.1  Dépôt de déploiement et runner")
p("Le projet GitLab <code>souverainrecrut-deploy</code> contient uniquement <code>ansible/</code>, <code>deployment/</code>, "
  "<code>terraform/</code> et <code>.gitlab-ci.yml</code>. Le <b>runner est installé sur la VM</b> : la machine est derrière le NAT d'un poste "
  "de travail, donc injoignable par les runners partagés de gitlab.com ; le runner, lui, <i>sort</i> vers GitLab pour récupérer ses "
  "jobs. Aucun port entrant n'est nécessaire.")
fig("gl-repo", "16-gitlab-depot-deploiement.jpg", "Dépôt GitLab de déploiement : le code applicatif n'y figure pas, seulement l'infrastructure et le pipeline.")
fig("gl-runner", "17-gitlab-runner-en-ligne.jpg", "Runner <code>souverainrecrut-vm</code> : en ligne, actif, dernier contact il y a quelques secondes (adresse IP masquée).")
h2("6.2  Variables et secrets")
p("Six variables alimentent le pipeline. Toutes sont <i>Protected</i> (disponibles seulement sur la branche protégée) ; les deux secrets "
  "applicatifs sont <i>Masked</i>. La clé SSH est de type <b>File</b>, ce qui évite qu'elle apparaisse dans un journal. Aucun jeton Docker Hub n'est défini : l'image est publique, et le pipeline n'exécute <code>docker login</code> (jeton par l'entrée standard, <code>docker logout</code> garanti) que si une variable <code>DOCKERHUB_TOKEN</code> existe.")
fig("gl-vars", "18-gitlab-variables-masquees.jpg", "Variables CI/CD : valeurs masquées par <code>•••••</code>, secrets « Masked », clé SSH de type « File », toutes « Protected ».")
h2("6.3  Les jobs et l'approbation manuelle")
table(["Job", "Déclenchement", "Rôle"], [
    ["<code>validate-tag</code>", "automatique", "vérifie le format <code>X.Y.Z-sha7</code> (jamais <code>latest</code>) et l'existence du tag sur Docker Hub (5 tentatives)"],
    ["<code>deploy-production</code>", "<b>manuel</b> (<code>when: manual</code>)", "copie les fichiers en SSH, reconstruit le <code>.env</code> depuis les variables, lance <code>deploy.sh</code>"],
    ["<code>smoke-test</code>", "automatique après le déploiement", "teste <code>/v1/health</code> et <code>/v1/ready</code>, compare l'image en production au tag demandé"],
    ["<code>rollback-production</code>", "<b>manuel</b>", "redéploie <code>PREVIOUS_TAG</code> et revérifie l'API"],
])
dia("gl-flow", d_gitlab(), "Pipeline GitLab : validation automatique, porte d'approbation humaine, vérification automatique, rollback disponible.")
fig("gl-pipe", "12-gitlab-pipeline-vert.jpg", "Pipeline #3049879562 : <code>validate-tag</code>, <code>deploy-production</code> (approuvé) et <code>smoke-test</code> réussis ; le rollback reste disponible.")
fig("gl-env", "13-gitlab-environnement-production.jpg", "Environnement « production » : déploiement réussi, déclenché par <code>@WakakiVongola</code> avec date et commit : c'est la <b>trace d'audit de l'approbation</b>. L'entrée « Waiting » est un pipeline ultérieur (commit <code>ae74a040</code>) dont personne n'a approuvé le déploiement : il n'est donc pas parti en production.")
fig("gl-smoke", "14-gitlab-smoke-test-log.jpg", "Journal du <code>smoke-test</code> : API <i>UP</i> et <i>READY</i>, conteneurs <i>healthy</i>, image en production égale au tag demandé.")

# ------------------------------------------------------------------ 7. Vérification et rollback
h1("7", "Vérification et rollback", "s7")
note("", "<b>En bref.</b> L'API répond READY, les données survivent aux redémarrages, et le retour arrière a été joué sur trois versions.")
h2("7.1  Vérifier le service")
p("Après déploiement, l'API est interrogée <b>depuis le poste hôte</b> (donc à travers le réseau et le pare-feu), et non depuis la VM. "
  "Une requête sans jeton doit être refusée : l'authentification est bien active en production.")
term("term-verif", "vérifications depuis le poste Windows", """
GET /v1/health      -> {"success":true,"data":{"status":"UP","environment":"production"}}
GET /v1/ready       -> {"success":true,"data":{"status":"READY","database":"CONNECTED"}}
GET /v1/candidates  (sans jeton) -> HTTP 401

souverainrecrut-backend  aarontiavin/souverainrecrut-backend:1.0.0-723d0f4  Up (healthy)  0.0.0.0:4000->4000/tcp
souverainrecrut-db       postgres:16-alpine                                  Up (healthy)  5432/tcp
""", "Contrôles de bout en bout : santé, connexion à la base, authentification, état des conteneurs.")
p("La <b>persistance</b> a été vérifiée en créant un candidat par l'API, puis en arrêtant et redémarrant toute la pile : "
  "la donnée est toujours là, car PostgreSQL écrit dans un volume Docker nommé.")
h2("7.2  Rollback testé sur trois versions")
p("Chaque déploiement mémorise le tag précédent. Le retour arrière redéploie une image <b>déjà publiée et déjà validée</b> par la chaîne : "
  "aucune reconstruction, donc rapide et sûr.")
dia("rollback", d_rollback(), "Scénario de rollback joué : de 723d0f4 à 12a585b puis retour à 723d0f4, avec les données conservées.")
table(["Étape", "Image en production", "<code>/v1/ready</code>", "Candidats en base"], [
    ["1. Déploiement initial", "<code>1.0.0-723d0f4</code>", "READY", "1 (créé par l'API)"],
    ["2. <code>./rollback.sh 1.0.0-12a585b</code>", "<code>1.0.0-12a585b</code>", "READY", "1"],
    ["3. <code>./rollback.sh 1.0.0-723d0f4</code>", "<code>1.0.0-723d0f4</code>", "READY", "1"],
])
term("term-rollback", "rollback.sh 1.0.0-12a585b", """
### AVANT : IMAGE_TAG=1.0.0-723d0f4
==> Rollback vers 1.0.0-12a585b
Tag précédent sauvegardé : 1.0.0-723d0f4
==> Pull aarontiavin/souverainrecrut-backend:1.0.0-12a585b
==> Vérification
OK : aarontiavin/souverainrecrut-backend:1.0.0-12a585b déployée et prête.
### APRES : IMAGE_TAG=1.0.0-12a585b | précédent=1.0.0-723d0f4
{"success":true,"data":{"status":"READY","database":"CONNECTED"}}
""", "Retour arrière réussi : l'ancienne version tourne, la base répond, le tag courant est mémorisé pour revenir en avant.")
note("warn", "<b>Ce test a trouvé un vrai bug.</b> Au premier essai, le rollback « réussissait » mais redéployait la version <i>courante</i> : "
             "<code>deploy.sh</code> rechargeait le fichier <code>.env</code> et écrasait le tag demandé. Corrigé (un tag passé en argument "
             "prime) puis rejoué avec succès. Sans ce test, la procédure documentée n'aurait pas fonctionné en situation réelle.")
h2("7.3  Limite : le schéma de base de données")
p("Le rollback applicatif <b>ne défait pas les migrations Prisma</b>. Pour qu'un retour arrière reste possible, les migrations doivent "
  "rester <i>additives</i> : nouvelle colonne nullable ou nouvelle table (ignorées par la version précédente), et jamais de renommage ni "
  "de suppression en une seule release (procéder en deux temps : <i>expand</i> puis <i>contract</i>). Une sauvegarde "
  "<code>pg_dump</code> précède toute migration risquée. État actuel : une seule migration, commune à toutes les versions publiées, "
  "donc aucun risque de schéma.")

# ------------------------------------------------------------------ 8. Traçabilité
h1("8", "Traçabilité du commit à la production", "s8")
note("", "<b>En bref.</b> La même empreinte (digest) de l'image du build Jenkins et du conteneur en production : l'artefact testé est celui déployé.")
p("Pour chaque déploiement, le cours demande de pouvoir retrouver le commit, le résultat du Quality Gate, le digest de l'image et "
  "l'approbation. Le <b>digest</b> est la pièce maîtresse : c'est l'empreinte de l'image, impossible à falsifier sans changer sa valeur.")
dia("trace", d_trace(), "Chaîne de traçabilité du déploiement de référence : le digest publié par Jenkins est le digest du conteneur en production.")
table(["Élément à conserver", "Valeur pour le déploiement de référence", "Où le retrouver", ""], [
    ["Commit et auteur", "<code>723d0f4</code> · Aaron-kun · 10/11 10:14", "GitHub, historique de <code>Dev</code>", OK],
    ["Résultat du Quality Gate", "Passed · 151 tests · 0 CRITICAL", f"Jenkins build #11, {R('cap-sonar')}", OK],
    ["Digest de l'image", "<code class=\"dg\">sha256:0b9848d00e9d21685eb0419dc9ccfe2a29a06fa18a26f0b86f7f034ed4e7773a</code>", f"console Jenkins ; {R('term-deploy')}", OK],
    ["Approbation : qui, quand", "WakakiVongola · 10/11/2026 15:03", f"GitLab → Environnements, {R('gl-env')}", OK],
    ["Inventaire des composants (SBOM)", "non produit", "perspective § 14", KO],
    ["Signature de l'image", "non réalisée", "perspective § 14", KO],
], "audit")

# ------------------------------------------------------------------ 9. Sécurité
h1("9", "Sécurité de la livraison", "s9")
note("", "<b>En bref.</b> Secrets hors du dépôt et masqués dans les journaux. Un incident (clé SSH affichée dans un journal) est traité et documenté.")
table(["Secret", "Où il est stocké", "Protection"], [
    ["Jeton SonarQube, accès Docker Hub", "credentials Jenkins", "injectés à l'exécution, masqués dans les logs"],
    ["Mot de passe PostgreSQL, clé de signature JWT", "variables GitLab <i>Masked</i> + <code>.env</code> du serveur", "fichier en mode 0600, reconstruit par le pipeline, jamais commité"],
    ["Clé SSH de déploiement", "variable GitLab de type <i>File</i>", "chemin temporaire effacé en fin de job"],
    ["Jetons d'accès GitLab et GitHub", "poste de l'étudiant, hors dépôt", "jamais écrits dans <code>.git/config</code>"],
])
p("Autres mesures : image non-root sans outils de build, pare-feu <i>deny</i> par défaut (seuls 22 et 4000 ouverts), PostgreSQL "
  "non exposé sur l'hôte, <code>.gitignore</code> sur <code>.env</code>, <code>*.tfvars</code>, <code>*.tfstate</code> et clés, balayage des secrets avant chaque commit.")
h2("Incident : une clé privée affichée dans un journal")
note("warn", "<b>Ce qui s'est passé.</b> La variable <code>SSH_PRIVATE_KEY</code> avait été créée en type <i>Variable</i> et non <i>File</i>. "
             "La commande <code>chmod 600 \"$SSH_PRIVATE_KEY\"</code> a reçu le <i>contenu</i> de la clé comme argument, a échoué, et son message "
             "d'erreur a recopié la clé dans le journal du job. Le projet étant privé et à membre unique, l'exposition est restée limitée.")
table(["Étape", "Action"], [
    ["Détection", "relecture du journal du job en échec"],
    ["Correction", "variable recréée en type <b>File</b> : le pipeline suivant ne laisse plus rien apparaître"],
    ["Nettoyage", "les deux journaux concernés ont été <b>effacés</b> (« Job has been successfully erased »)"],
    ["Décision", "clé conservée (projet pédagogique) ; en production réelle : rotation de la clé et retrait de l'ancienne sur le serveur"],
])
p("<b>Leçon.</b> Un secret sur plusieurs lignes ne peut pas être masqué par GitLab ; seul le type <i>File</i> garantit qu'il ne s'affiche pas. "
  "C'est désormais écrit dans la procédure de déploiement.")

# ------------------------------------------------------------------ 10. Défauts
h1("10", "Qualité du code de référence : défauts identifiés", "s10")
note("", "<b>En bref.</b> Huit défauts du code de référence : six révélés par les tests, deux signalés par SonarQube. Tous sont tracés, aucun n'est masqué.")
p("La revue de la suite de tests a révélé des défauts du dépôt de référence. Le périmètre interdit de modifier <code>backend/src/</code> : "
  "ils sont donc <b>tracés, pas corrigés</b>. Chacun est décrit par un test marqué <code>it.failing</code> : le test exprime le comportement "
  "<i>attendu</i>, échoue aujourd'hui (donc compte comme réussi), et fera échouer le pipeline le jour où le défaut sera corrigé sans mise à jour du test.")
table(["#", "Défaut", "Gravité", "Comportement attendu"], [
    ["D1", "<code>PUT /users/:id</code> avec un mot de passe : <b>stocké en clair</b> (pas de hachage à la mise à jour)", "Critique", "hachage bcrypt, comme à la création"],
    ["D2", "<code>GET /users</code> et <code>/users/:id</code> renvoient le <b>hash bcrypt</b> des utilisateurs", "Haute", "champ <code>password</code> absent de la réponse"],
    ["D3", "<code>POST /auth/login</code> sans validation : corps vide → erreur 401 au lieu de 400", "Moyenne", "validation Zod → 400"],
    ["D4", "<code>?page=abc</code> donne <code>skip: NaN</code> puis une erreur serveur", "Moyenne", "repli sur la page 1"],
    ["D5", "Clé étrangère violée (<code>P2003</code>) non traduite → 500", "Moyenne", "400 ou 404 explicite"],
    ["D6", "Un recruteur peut créer une offre au nom d'un autre (pas de contrôle de propriété)", "Moyenne", "403, ou identifiant forcé à celui du jeton"],
    ["D7", "Express annonce sa version (en-tête <code>X-Powered-By</code>) : information utile à un attaquant <i>(SonarQube, sécurité)</i>", "Faible", "<code>app.disable('x-powered-by')</code> ou Helmet"],
    ["D8", "<code>parseInt</code> au lieu de <code>Number.parseInt</code>, deux occurrences dans <code>pagination.ts</code> <i>(SonarQube, fiabilité)</i> ; lié à D4", "Faible", "<code>Number.parseInt</code> avec valeur par défaut"],
])
p("Les défauts D7 et D8 sont les trois problèmes ouverts signalés par SonarQube (§ 4.2) : ils existent depuis la version de référence. "
  "Le Quality Gate ne porte que sur le <i>nouveau</i> code, qui n'en contient aucun : c'est pourquoi il reste « Passed ».")
note("", "<b>Pourquoi c'est important pour la chaîne.</b> Un pipeline entièrement vert ne prouve pas l'absence de défaut : "
         "il prouve que ce qui est contrôlé est conforme. Documenter ce qui n'est <i>pas</i> contrôlé est une exigence d'honnêteté technique.")

# ------------------------------------------------------------------ 11. Performances et incidents
h1("11", "Performances et incidents", "s11")
note("", "<b>En bref.</b> Quatre échecs de build instructifs, puis des builds plus rapides. Migration de base : de 4 min 40 s à 13 s.")
h2("11.1  Évolution des builds")
p("Quatre builds ont échoué avant la stabilisation (#5 à #8), chacun révélant un vrai problème (voir § 11.3). La durée est ensuite passée "
  "de plus de 7 minutes à environ 70 secondes, en grande partie grâce aux caches (dépendances npm, couches Docker, base de vulnérabilités Trivy). "
  "Les quatre premiers builds ont été purgés par la rotation des historiques (10 conservés).")
dia("builds", d_builds(), "Durée et résultat des builds Jenkins #5 à #14 : quatre échecs instructifs, puis six succès de plus en plus rapides.")
h2("11.2  Optimisation de la migration de base de données")
p("Dans le premier pipeline GitLab, la migration Prisma durait <b>4 min 40 s</b> : la CLI était retéléchargée depuis npm à chaque déploiement. "
  "Un volume Docker conserve désormais son cache npm : la migration passe à <b>13 s</b> (mesuré sur la VM), soit environ vingt fois plus vite.")
dia("migration", d_migration(), "Durée de la migration Prisma avant et après l'ajout d'un cache npm persistant.")
h2("11.3  Incidents rencontrés et leçons")
table(["Phase", "Incident", "Cause racine", "Leçon"], [
    ["CI", "Aucun test exécuté, client Prisma absent", "dépôt fourni sans configuration de tests ; scripts <code>postinstall</code> bloqués", "<code>prisma generate</code> en étape dédiée"],
    ["CI", "Seuil de couverture ignoré", "faute de frappe (<code>coverageThresholds</code>)", "vérifier qu'une règle <i>bloque</i> réellement"],
    ["CI", "Mot de passe SonarQube perdu, webhook refusé", "échappement du <code>$</code> sous PowerShell ; réseau privé interdit par défaut", "tester les commandes dans l'interpréteur cible"],
    ["CI", "Jenkins sans docker, Node ni Trivy", "image officielle trop minimale", "image Jenkins personnalisée et versionnée"],
    ["CI", "<code>NullPointerException</code> au checkout", "<code>skipDefaultCheckout</code> ne définit pas <code>GIT_COMMIT</code>", "lire le résultat de <code>checkout scm</code>"],
    ["CI", "Publication bloquée par 2 CVE CRITICAL", "dépendance Express et npm embarqué dans l'image", "le scan a joué son rôle de barrière"],
    ["CI", "Credential Docker Hub absent", "oubli de configuration", "journal d'étapes bloquantes (<i>runbook</i>)"],
    ["Déploiement", "Rollback vers la mauvaise version", "<code>.env</code> écrasait le tag demandé", "tester le retour arrière pour de vrai"],
    ["Déploiement", "Clé privée affichée dans un journal", "variable de type Variable au lieu de File", "voir § 9"],
    ["Déploiement", "YAML refusé par GitLab", "<code>: </code> dans une commande non quotée", "valider dans l'éditeur de pipeline"],
    ["Déploiement", "Coupures réseau de la VM (curl code 56)", "instabilité du NAT VMware", "tentatives répétées, scripts idempotents"],
], "incidents")

# ------------------------------------------------------------------ 12. DORA
h1("12", "Indicateurs DORA et Definition of Done", "s12")
note("", "<b>En bref.</b> Quatre indicateurs DORA mesurés sur la période, et la définition de « livraison terminée ».")
p("Les quatre indicateurs DORA mesurent la performance d'une chaîne de livraison. Valeurs relevées sur les deux jours du projet "
  "(échantillon très court : ils illustrent la méthode, ils ne sont pas statistiquement significatifs).")
table(["Indicateur", "Valeur mesurée", "Source"], [
    ["Fréquence de déploiement", "6 tentatives sur le serveur en une journée, dont 4 réussies", "journaux de <code>deploy.sh</code> et GitLab"],
    ["Délai de livraison (commit → image publiée)", "≈ 10 min (≤ 5 min d'attente du <i>Poll SCM</i> + 70 à 100 s de build)", "Jenkins #13 et #14"],
    ["Délai image → production", "pipeline GitLab de 3 à 8 min + délai d'approbation", "GitLab"],
    ["Taux d'échec des déploiements", "2 échecs sur 6 tentatives (33 %), tous deux détectés avant impact durable", "voir § 11.3"],
    ["Temps de restauration", "2 à 4 min (retour à la version précédente, téléchargement compris)", f"{R('term-rollback')}"],
], "dora")
h2("Definition of Done : une livraison est « terminée » quand…")
table(["Critère", "État"], [
    ["Le pipeline Jenkins est vert (tests, Quality Gate, Trivy)", f"{OK} builds #9 à #14"],
    ["L'image est publiée avec un tag traçable", f"{OK} <code>1.0.0-sha7</code>"],
    ["Le déploiement est approuvé et tracé", f"{OK} {R('gl-env')}"],
    ["Le service est vérifié après déploiement", f"{OK} {R('gl-smoke')}"],
    ["Un retour arrière est documenté et testé", f"{OK} § 7"],
    ["La documentation est à jour", f"{OK} annexe A"],
])
note("", "<b>Rétrospective.</b> Les échecs les plus coûteux étaient tous des problèmes d'<i>environnement</i> (réseau de la VM, échappement de commandes, "
         "types de variables), pas de logique. Trois pratiques ont fait gagner du temps : tout rejouer à la main avant d'automatiser, "
         "tenir un journal des étapes bloquantes, et vérifier chaque correctif par une exécution réelle.")

# ------------------------------------------------------------------ 13. MSPR
h1("13", "Argumentaire MSPR 4.1 et 5.1", "s13")
note("", "<b>En bref.</b> Les arguments pour les deux modules (MSPR 4.1 et 5.1), chacun relié à sa preuve.")
h2("MSPR 4.1 · Valeur ajoutée de l'automatisation (Jour 1)")
table(["Sans automatisation", "Avec la chaîne mise en place"], [
    ["Tests, analyse, build et publication lancés à la main, dans un ordre variable", "un <i>Jenkinsfile</i> exécute toujours les mêmes dix étapes, à chaque commit"],
    ["Une faille peut atteindre le registre sans que personne ne la voie", "deux publications ont été <b>bloquées</b> par Trivy avant d'exister"],
    ["Build de plus de 7 minutes, résultat à interpréter", "70 à 100 secondes, verdict binaire, rapports archivés"],
    ["Version déployée difficile à relier au code", "tag <code>version-sha</code> et digest vérifiable"],
], "cmp")
h2("MSPR 5.1 · Déploiement fiable, réversible, conforme (Jour 2)")
table(["Critère", "Argument", "Preuve"], [
    ["Choix d'outils justifiés", "chaque outil répond à une exigence du cahier ; les écarts sont expliqués (§ 3, § 14)", "tableau des outils"],
    ["Déploiement fiable", "image unique testée puis déployée telle quelle ; vérification automatique après déploiement", f"{R('trace')}, {R('gl-smoke')}"],
    ["Déploiement réversible", "rollback joué sur trois versions, données conservées, limites de schéma documentées", f"{R('rollback')}"],
    ["Preuves de conformité", "audit trail, approbation tracée, journaux et rapports archivés", f"{R('gl-env')}, annexe A"],
], "cmp")

# ------------------------------------------------------------------ 14. Écarts
h1("14", "Écarts, limites et perspectives", "s14")
note("", "<b>En bref.</b> Ce qui n'est pas réalisé, pourquoi, et comment le compléter.")
h2("Écarts assumés par rapport au cahier")
table(["Écart", "Raison", "Impact"], [
    ["Ubuntu 22.04 au lieu de 24.04", "VM mise à disposition", "aucun sur Docker, Compose ou Ansible"],
    ["Terraform ne crée pas la VM", "VMware Workstation sans ESXi/vCenter (prévu au § 4.2 du cahier)", "Terraform contrôle le serveur et génère l'inventaire"],
    ["Pas de HTTPS", "environnement de laboratoire", "API en HTTP sur réseau local ; reverse proxy TLS à ajouter"],
    ["Pas d'environnement de <i>staging</i>", "non exigé par le cahier", "un seul environnement, protégé par l'approbation manuelle"],
    ["Pas de jeton Docker Hub dans GitLab (§ 4.4)", "image publique : le pull anonyme suffit ; un secret de moins à gérer", "le pipeline fait le <code>docker login</code> dès qu'une variable <code>DOCKERHUB_TOKEN</code> est ajoutée (nécessaire si l'image devient privée)"],
])
h2("Ce qui n'a pas été réalisé")
table(["Élément", "Pourquoi", "Comment l'ajouter"], [
    ["SBOM (inventaire des composants)", "option du cours, non exigée par le cahier", "étape Jenkins <code>syft scan</code> + archivage du fichier CycloneDX"],
    ["Signature d'image (<code>cosign</code>)", "option du cours", "signer après le push, vérifier avant le déploiement"],
    ["Tests de charge (<code>k6</code>)", "option du cours", "étape optionnelle après le <i>smoke-test</i>"],
    ["Tests d'intégration sur un vrai PostgreSQL", "la suite simule la base", "PostgreSQL éphémère dans le pipeline Jenkins"],
])
h2("Perspectives")
table(["Amélioration", "Intérêt"], [
    ["Déclencher le pipeline GitLab depuis Jenkins (API de déclenchement) en gardant l'approbation manuelle", "« du commit à la production en un clic »"],
    ["Environnement protégé GitLab, approbateurs restreints", "limiter qui peut mettre en production"],
    ["Renouvellement périodique de la clé SSH et des jetons", "réduire l'exposition des secrets"],
    ["Corriger les défauts D1 à D8 dans le code applicatif", "fermer les failles identifiées au § 10"],
])

# ------------------------------------------------------------------ Annexes
h1("A", "Annexes", "annexes")
h2("A. Contenu du livrable")
p("Le livrable est assemblé dans l'arborescence du cahier (§ 6) par <code>livrable/assembler-livrable.py</code>, qui refuse de "
  "produire l'archive s'il détecte un jeton, une clé privée ou une adresse IP publique. Archive : <code>SouverainRecrut-CICD.zip</code> (84 fichiers).")
add("""<pre class="tree">SouverainRecrut-CICD/
├── README.md                  ← point d'entrée + correspondance avec les chemins du dépôt GitHub
├── integration-continue/      ← Jour 1
│   ├── Jenkinsfile · Dockerfile · .dockerignore · README.md · etapes-bloquantes.md (runbook)
│   ├── sonar/                 sonar-project.properties
│   ├── tests/                 jest.config.js · tests/ (18 suites) · export-openapi.ts
│   ├── stack-ci/              docker-compose.yml (Jenkins, SonarQube) · jenkins/Dockerfile
│   ├── reports/               JUnit · lcov · Trivy · OpenAPI + doc HTML · console Jenkins · preuves de déploiement
│   └── captures/              19 captures d'écran
├── deploiement/               ← Jour 2
│   ├── terraform/             providers.tf · main.tf · variables.tf · outputs.tf · README.md
│   ├── ansible/               inventory.ini · playbook.yml · run-ansible.ps1
│   ├── deployment/            docker-compose.yml · .env.example · deploy.sh · rollback.sh
│   ├── .gitlab-ci.yml
│   └── README.md
└── documentation/             architecture.md · procedure-deploiement.md · procedure-rollback.md
                               rapport-final.md · rapport/rapport-final.pdf · suivi-livrables.md</pre>""")
h2("B. Rejouer le déploiement")
add("""<pre class="tree">cd deploiement/terraform &amp;&amp; cp terraform.tfvars.example terraform.tfvars        # adapter vm_ip, ssh_user
terraform init &amp;&amp; terraform validate &amp;&amp; terraform plan &amp;&amp; terraform apply     # (dans l'image hashicorp/terraform)
powershell -ExecutionPolicy Bypass -File deploiement\\ansible\\run-ansible.ps1 --nopass --check --diff
powershell -ExecutionPolicy Bypass -File deploiement\\ansible\\run-ansible.ps1 --nopass
# GitLab : créer le runner (tag souverainrecrut-vm), les 6 variables, puis Build &gt; Pipelines &gt; New pipeline
# Approuver deploy-production (▶), vérifier smoke-test
curl http://&lt;ip&gt;:4000/v1/ready                      # {"status":"READY","database":"CONNECTED"}
ssh &lt;user&gt;@&lt;ip&gt; "cd /opt/souverainrecrut &amp;&amp; ./rollback.sh 1.0.0-12a585b"    # retour arrière</pre>""")
h2("C. Glossaire")
table(["Terme", "Définition"], [
    ["CI / intégration continue", "chaque commit est compilé et testé automatiquement"],
    ["Livraison continue", "l'artefact est toujours prêt à déployer ; la mise en production est validée par un humain"],
    ["Déploiement continu", "chaque changement validé part en production sans intervention"],
    ["Quality Gate", "règles de qualité (couverture, vulnérabilités, duplications) dont l'échec bloque le pipeline"],
    ["Trivy", "outil qui détecte les vulnérabilités d'une image Docker"],
    ["Tag / digest", "le tag est un nom lisible (<code>1.0.0-723d0f4</code>) ; le digest est l'empreinte unique du contenu de l'image"],
    ["Runner", "programme qui exécute les jobs d'un pipeline GitLab"],
    ["Idempotent", "qu'on peut rejouer sans effet de bord : le second passage ne change rien"],
    ["Rollback", "retour à une version précédente"],
    ["SBOM", "<i>Software Bill of Materials</i> : liste des composants d'un logiciel"],
    ["DORA", "quatre indicateurs de performance de la livraison logicielle"],
], "gloss")
add('<div class="pbreak"></div>')
h2("D. Index des figures")
add('<ol class="figlist">' + "".join(
    f'<li><a href="#fig-{fid}"><b>Figure {n}</b></a> — {cap}</li>' for fid, n, cap in FIGS) + "</ol>")

# ============================================================================ ASSEMBLAGE
CSS = """
@page { size: A4; margin: 17mm 15mm 19mm 15mm;
  @bottom-center { content: counter(page) " / " counter(pages); font: 8pt 'Segoe UI', Arial; color: #64748b; }
  @top-right { content: "SouverainRecrut · Rapport final CI/CD"; font: 8pt 'Segoe UI', Arial; color: #94a3b8; } }
@page :first { margin: 0; @bottom-center { content: none; } @top-right { content: none; } }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 9.6pt; line-height: 1.5; color: #1e293b; margin: 0; }
a { color: #1d4ed8; text-decoration: none; }
h1 { font-size: 19pt; color: #0f172a; margin: 0 0 10px; padding: 6px 0 8px; border-bottom: 3px solid #2563eb; break-after: avoid; display: flex; align-items: center; gap: 12px; }
h1 span { background: #2563eb; color: #fff; border-radius: 8px; min-width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; font-size: 15pt; padding: 0 8px; }
h1.pb { break-before: page; }
h2 { font-size: 12.5pt; color: #1d4ed8; margin: 16px 0 6px; break-after: avoid; }
p { margin: 6px 0 8px; text-align: justify; }
code { font-family: Consolas, monospace; font-size: 8.6pt; background: #f1f5f9; padding: 0 4px; border-radius: 3px; color: #0f172a; overflow-wrap: break-word; }
code.dg { word-break: break-all; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 12px; font-size: 8.8pt; }
th { background: #0f172a; color: #fff; text-align: left; padding: 5px 8px; font-weight: 600; }
td { padding: 4px 8px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f8fafc; }
tr { break-inside: avoid; }
table.audit, table.dora, table.cmp, table.gloss { break-inside: avoid; }
.pbreak { break-before: page; }
figure { margin: 10px 0 14px; break-inside: avoid; text-align: center; }
figure img { width: 100%; border: 1px solid #cbd5e1; border-radius: 6px; box-shadow: 0 1px 4px rgba(15,23,42,.18); }
figure.dia svg { width: 100%; height: auto; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; padding: 4px; }
figcaption { font-size: 8.4pt; color: #475569; margin-top: 5px; text-align: left; padding: 0 4px; }
figcaption b { color: #1d4ed8; }
.term { background: #0f172a; border-radius: 8px; overflow: hidden; text-align: left; }
.termbar { background: #1e293b; padding: 5px 10px; display: flex; align-items: center; gap: 6px; }
.termbar i { width: 9px; height: 9px; border-radius: 50%; background: #475569; display: inline-block; }
.termbar i:nth-child(1) { background: #ef4444; } .termbar i:nth-child(2) { background: #f59e0b; } .termbar i:nth-child(3) { background: #22c55e; }
.termbar span { color: #94a3b8; font: 8pt Consolas, monospace; margin-left: 8px; }
.term pre { margin: 0; padding: 9px 12px; color: #e2e8f0; font: 7.7pt/1.45 Consolas, monospace; white-space: pre-wrap; word-break: break-all; }
.note { border-left: 5px solid #2563eb; background: #eff6ff; padding: 7px 12px; margin: 10px 0; border-radius: 0 6px 6px 0; break-inside: avoid; font-size: 9.2pt; }
.note.ok { border-color: #16a34a; background: #f0fdf4; }
.note.warn { border-color: #ea580c; background: #fff7ed; }
.kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 12px 0; }
.kpi { border: 1px solid #dbeafe; border-left: 5px solid #2563eb; border-radius: 8px; padding: 8px 12px; background: #fff; }
.kpi.g { border-left-color: #16a34a; } .kpi.o { border-left-color: #ea580c; }
.kpi b { display: block; font-size: 22pt; color: #0f172a; line-height: 1.1; }
.kpi span { font-size: 8.6pt; color: #475569; }
.cover { width: 210mm; height: 297mm; padding: 16mm 16mm 14mm; background: linear-gradient(160deg, #0f172a 0%, #1e3a8a 62%, #2563eb 100%); color: #fff; display: flex; flex-direction: column; justify-content: space-between; break-after: page; }
.cover-top { font-size: 9pt; letter-spacing: .4px; color: #bfdbfe; }
.cover-kicker { font-size: 10.5pt; color: #93c5fd; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1.2px; }
.cover h1.cover-title { font-size: 34pt; line-height: 1.12; color: #fff; border: 0; display: block; padding: 0; margin: 0 0 12px; }
.cover-sub { font-size: 12pt; color: #dbeafe; line-height: 1.55; margin-bottom: 22px; }
.cover-art { background: rgba(255,255,255,.96); border-radius: 14px; padding: 10px; }
.cover-art svg { width: 100%; height: auto; display: block; }
.cover-meta { width: 100%; border-collapse: collapse; font-size: 9.6pt; }
.cover-meta td { border-bottom: 1px solid rgba(255,255,255,.25); padding: 5px 4px; background: transparent !important; color: #e0f2fe; }
.cover-meta td:first-child { width: 36%; color: #93c5fd; }
.cover a { color: #fff; text-decoration: underline; font-weight: 600; }
.toc { break-after: page; padding-top: 6mm; }
.toc-title { font-size: 20pt; color: #0f172a; margin: 0 0 12px; border-bottom: 3px solid #2563eb; padding-bottom: 6px; }
.toc ol { list-style: none; counter-reset: s; padding: 0; margin: 0; }
.toc li { counter-increment: s; display: flex; align-items: baseline; gap: 10px; padding: 7px 0; border-bottom: 1px solid #e2e8f0; font-size: 11pt; }
.toc li::before { content: counter(s); background: #2563eb; color: #fff; border-radius: 6px; min-width: 24px; text-align: center; font-size: 9.5pt; font-weight: 700; padding: 1px 0; }
.toc li:last-child::before { content: "A"; }
.toc li a { font-weight: 600; color: #0f172a; }
.toc li span { color: #64748b; font-size: 9.2pt; margin-left: auto; }

.glance { break-after: page; padding-top: 2mm; }
.glance .lead { font-size: 11pt; color: #0f172a; background: #eff6ff; border-radius: 8px; padding: 10px 14px; margin: 8px 0 12px; }
table.glance-t td:first-child { font-weight: 600; color: #0f172a; width: 30%; }
table.glance-t td { font-size: 9pt; }
.retenir { border: 2px solid #2563eb; border-radius: 10px; padding: 10px 14px; margin-top: 12px; background: #fff; break-inside: avoid; }
.retenir ol { margin: 6px 0 0 18px; padding: 0; } .retenir li { margin: 4px 0; }
pre.tree { background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px 12px; font: 8pt/1.5 Consolas, monospace; white-space: pre-wrap; break-inside: avoid; }
ol.figlist { font-size: 8.4pt; padding-left: 18px; columns: 1; } ol.figlist li { margin: 2px 0; list-style: none; margin-left: -18px; }
table.audit td:last-child, table.dora td:first-child { white-space: nowrap; }
"""

PB = ["s1", "s2", "s4", "s5", "s6", "s7", "annexes"]
body = "\n".join(PARTS)
for fid in PB:
    body = body.replace(f'<h1 id="{fid}">', f'<h1 id="{fid}" class="pb">')
for fid, n, _ in FIGS:
    body = body.replace(f"§§{fid}§§", f'<a href="#fig-{fid}">Figure {n}</a>')
missing = sorted(set(re.findall(r"§§([^§]+)§§", body)))
if missing:
    raise SystemExit(f"Références de figures introuvables : {missing}")

page = (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>SouverainRecrut — Rapport final CI/CD</title>'
        f"<style>{CSS}</style></head><body>{body}</body></html>")
(HERE / "rapport-final.html").write_text(page, encoding="utf-8")
print(f"rapport-final.html : {len(FIGS)} figures, {len(page) // 1024} Ko")


# ============================================================================ PDF (option --pdf)
def construire_pdf():
    import os
    import subprocess
    import sys  # noqa: F401
    import fitz  # PyMuPDF

    chrome = next((c for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                               r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") if os.path.exists(c)), None)
    if not chrome:
        raise SystemExit("Chrome ou Edge introuvable")
    pdf = HERE / "rapport-final.pdf"
    pdf.unlink(missing_ok=True)
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=10000",
                    f"--print-to-pdf={pdf}", (HERE / "rapport-final.html").as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    doc = fitz.open(pdf)
    titres = {"s1": "1  Résumé exécutif", "s2": "2  Contexte, objectifs et démarche", "s3": "3  Architecture de la chaîne",
              "s4": "4  Jour 1 · Intégration continue", "s5": "5  Jour 2 · Serveur et déploiement", "s6": "6  Pipeline GitLab CI/CD",
              "s7": "7  Vérification et rollback", "s8": "8  Traçabilité du commit à la production", "s9": "9  Sécurité de la livraison",
              "s10": "10  Qualité du code de référence", "s11": "11  Performances et incidents",
              "s12": "12  Indicateurs DORA et Definition of Done", "s13": "13  Argumentaire MSPR 4.1 et 5.1",
              "s14": "14  Écarts, limites et perspectives", "annexes": "Annexes"}
    cible = {l["nameddest"]: l["page"] + 1 for pg in doc for l in pg.get_links() if l.get("nameddest") in titres}
    doc.set_toc([[1, "Sommaire", next(i + 1 for i, pg in enumerate(doc) if "Sommaire" in pg.get_text())]] + [[1, t, cible[k]] for k, t in titres.items()] + [[1, "Index des figures", len(doc)]])
    doc.save(str(pdf) + ".tmp", garbage=3, deflate=True)
    doc.close()
    os.replace(str(pdf) + ".tmp", pdf)
    print(f"rapport-final.pdf : {fitz.open(pdf).page_count} pages, {pdf.stat().st_size // 1024} Ko, signets ajoutés")


if "--pdf" in __import__("sys").argv:
    construire_pdf()
