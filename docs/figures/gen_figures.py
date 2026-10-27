"""Generate all schematic diagrams for the NestQuest final-year project report.

Run:  python docs/figures/gen_figures.py
Outputs PNG files into the same folder (docs/figures/).
Only the matplotlib stack is required (already a project dependency).
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse

OUT = os.path.dirname(os.path.abspath(__file__))

PRIMARY = "#1f4b99"
ACCENT = "#f0793b"
INK = "#0b1628"
GREY = "#55607a"
FILL = "#eaf0fb"
FILL2 = "#fdece0"
FILL3 = "#e8f5ee"
GREEN = "#1f9d61"


def _fig(w=10.0, h=6.5):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc=FILL, ec=PRIMARY, fs=9, tc=INK, bold=False, round=True):
    style = "round,pad=0.3,rounding_size=2.2" if round else "square,pad=0.3"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight=("bold" if bold else "normal"), wrap=True)


def ell(ax, x, y, w, h, text, fc=FILL3, ec=GREEN, fs=8):
    ax.add_patch(Ellipse((x + w / 2, y + h / 2), w, h, fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, wrap=True)


def arrow(ax, x1, y1, x2, y2, text=None, color=GREY, style="-|>", lw=1.3, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=12, color=color, lw=lw, linestyle=ls,
                                 shrinkA=2, shrinkB=2))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, text, fontsize=7, color=color,
                ha="center", va="center", backgroundcolor="white")


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- Fig 3.1
def existing_workflow():
    fig, ax = _fig(11, 3.2)
    xs = [2, 22, 42, 62, 82]
    labels = ["Buyer /\nTenant", "Contacts\nBroker", "Broker shortlists\n(limited, biased)",
              "Site visits &\nnegotiation", "Deal + 1-2%\nbrokerage"]
    for i, (x, t) in enumerate(zip(xs, labels)):
        box(ax, x, 38, 16, 24, t, fc=(FILL2 if i in (2, 4) else FILL),
            ec=(ACCENT if i in (2, 4) else PRIMARY), fs=8.5)
        if i < len(xs) - 1:
            arrow(ax, x + 16, 50, x + 20, 50)
    ax.text(50, 15, "Information asymmetry · opaque pricing · brokerage cost · slow turnaround",
            ha="center", fontsize=9, color=ACCENT, style="italic")
    save(fig, "fig3_1_existing.png")


# ---------------------------------------------------------------- Fig 3.2
def proposed_workflow():
    fig, ax = _fig(11, 3.4)
    xs = [1.5, 21, 40.5, 60, 79.5]
    labels = ["Owner posts\nlisting (free)", "AI price check\n+ moderation",
              "Buyer searches\n& filters", "Direct enquiry\nto owner", "Owner replies —\nno broker"]
    for i, (x, t) in enumerate(zip(xs, labels)):
        box(ax, x, 40, 17, 24, t, fc=FILL3, ec=GREEN, fs=8.5)
        if i < len(xs) - 1:
            arrow(ax, x + 17, 52, x + 20, 52, color=GREEN)
    ax.text(50, 18, "Transparent · zero brokerage · data-driven pricing · self-service",
            ha="center", fontsize=9, color=GREEN, style="italic")
    save(fig, "fig3_2_proposed.png")


# ---------------------------------------------------------------- Fig 4.1
def architecture():
    fig, ax = _fig(10.5, 8.2)
    box(ax, 8, 86, 84, 11, "Presentation Layer — Jinja2 server-rendered pages + vanilla JS (app.js) + CSS",
        fc=FILL2, ec=ACCENT, fs=9.5, bold=True)
    box(ax, 8, 70, 84, 12,
        "Application Layer — FastAPI (Uvicorn ASGI)\nRouters: auth · properties · enquiries · admin · ml · uploads · pages",
        fc=FILL, ec=PRIMARY, fs=9.5, bold=True)
    # cross cutting
    box(ax, 8, 54, 40, 12, "Security — bcrypt hashing +\nJWT in httpOnly cookie\n(deps: optional/current/admin user)", fs=8.5)
    box(ax, 52, 54, 40, 12, "ML Engine — scikit-learn\nLinear Regression price estimator\n(backend/ml/predict.py)", fs=8.5)
    box(ax, 8, 38, 40, 12, "Business logic — Pydantic models,\nserializers, option lists, seeding", fs=8.5)
    box(ax, 52, 38, 40, 12, "Integration — Cloudinary image\nuploads · SMTP email (optional)", fs=8.5)
    box(ax, 8, 20, 84, 11, "Data Access Layer — Motor (async MongoDB driver) · ensure_indexes()",
        fc=FILL, ec=PRIMARY, fs=9.5, bold=True)
    box(ax, 8, 4, 40, 11, "MongoDB Atlas (cloud)\nusers · properties · enquiries\nsaved · predictions", fc=FILL3, ec=GREEN, fs=8.5, bold=True)
    box(ax, 52, 4, 40, 11, "External services\nCloudinary CDN · SMTP server", fc=FILL3, ec=GREEN, fs=8.5, bold=True)
    for y1, y2 in [(86, 82), (70, 66), (54, 50), (38, 31), (20, 15)]:
        arrow(ax, 50, y1, 50, y2, style="<|-|>")
    save(fig, "fig4_1_architecture.png")


# ---------------------------------------------------------------- Fig 4.2
def block_diagram():
    fig, ax = _fig(10.5, 6.2)
    box(ax, 2, 42, 18, 18, "User\n(browser)", fc=FILL2, ec=ACCENT, bold=True)
    box(ax, 30, 70, 20, 14, "Auth &\nSession", fs=8.5)
    box(ax, 30, 50, 20, 14, "Listings &\nSearch", fs=8.5)
    box(ax, 30, 30, 20, 14, "Enquiries &\nShortlist", fs=8.5)
    box(ax, 30, 10, 20, 14, "AI Price\nEstimator", fs=8.5)
    box(ax, 62, 60, 18, 14, "FastAPI\ncontroller", fc=FILL, ec=PRIMARY, bold=True, fs=8.5)
    box(ax, 62, 30, 18, 14, "ML model\n(.pkl)", fc=FILL3, ec=GREEN, bold=True, fs=8.5)
    box(ax, 86, 44, 12, 16, "MongoDB", fc=FILL3, ec=GREEN, bold=True, fs=8.5)
    box(ax, 86, 20, 12, 14, "Cloudinary", fc=FILL3, ec=GREEN, fs=8)
    arrow(ax, 20, 51, 30, 57)
    arrow(ax, 20, 51, 30, 37)
    for y in (77, 57, 37, 17):
        arrow(ax, 50, y, 62, (67 if y > 40 else 37))
    arrow(ax, 80, 67, 86, 55)
    arrow(ax, 80, 37, 86, 45, color=GREEN)
    arrow(ax, 80, 64, 86, 26, color=GREEN, ls="--", text="images")
    save(fig, "fig4_2_block.png")


# ---------------------------------------------------------------- Fig 4.3
def component_interaction():
    fig, ax = _fig(10.5, 6.0)
    box(ax, 2, 42, 16, 14, "Browser", fc=FILL2, ec=ACCENT, bold=True)
    box(ax, 24, 42, 16, 14, "pages.py\n(Jinja2)", fs=8.5)
    box(ax, 24, 70, 16, 12, "api routers", fs=8.5)
    box(ax, 46, 56, 16, 12, "deps.py\n(auth)", fs=8.5)
    box(ax, 46, 36, 16, 12, "models.py\n(Pydantic)", fs=8.5)
    box(ax, 46, 16, 16, 12, "ml/predict.py", fc=FILL3, ec=GREEN, fs=8.5)
    box(ax, 70, 46, 16, 12, "database.py\n(Motor)", fc=FILL, ec=PRIMARY, bold=True, fs=8.5)
    box(ax, 70, 24, 16, 12, "cloudinary_\nservice.py", fc=FILL3, ec=GREEN, fs=8)
    box(ax, 90, 46, 8, 12, "Atlas", fc=FILL3, ec=GREEN, fs=8)
    arrow(ax, 18, 49, 24, 49, style="<|-|>")
    arrow(ax, 10, 56, 32, 70, style="<|-|>", text="fetch/JSON")
    arrow(ax, 40, 74, 46, 62)
    arrow(ax, 40, 74, 46, 42)
    arrow(ax, 40, 74, 54, 28, ls="--")
    arrow(ax, 62, 50, 70, 52)
    arrow(ax, 62, 22, 70, 30, color=GREEN)
    arrow(ax, 86, 52, 90, 52, color=GREEN)
    save(fig, "fig4_3_component.png")


# ---------------------------------------------------------------- Fig 4.4
def use_case():
    fig, ax = _fig(10.5, 8.2)
    # actors
    for (x, y, name) in [(3, 72, "Guest"), (3, 42, "Registered\nUser"), (3, 12, "Admin")]:
        ax.plot([x + 3], [y + 10], marker="o", ms=10, color=PRIMARY)
        ax.plot([x + 3, x + 3], [y + 9, y + 2], color=PRIMARY, lw=2)
        ax.plot([x, x + 6], [y + 6, y + 6], color=PRIMARY, lw=2)
        ax.plot([x + 3, x], [y + 2, y - 4], color=PRIMARY, lw=2)
        ax.plot([x + 3, x + 6], [y + 2, y - 4], color=PRIMARY, lw=2)
        ax.text(x + 3, y - 8, name, ha="center", fontsize=8.5, color=INK)
    # system boundary
    ax.add_patch(FancyBboxPatch((20, 3), 76, 92, boxstyle="round,pad=0.3",
                                fc="none", ec=GREY, lw=1.2, linestyle="--"))
    ax.text(58, 97, "NestQuest System", ha="center", fontsize=10, color=GREY, fontweight="bold")
    cases = [
        (24, 84, "Browse / search listings"), (60, 84, "View property detail"),
        (24, 72, "Use AI price estimator"), (60, 72, "Sign up / Log in"),
        (24, 60, "Post / edit listing"), (60, 60, "Upload images (Cloudinary)"),
        (24, 48, "Shortlist property"), (60, 48, "Send / reply enquiry"),
        (24, 36, "Manage profile & dashboard"), (60, 36, "Moderate listings"),
        (24, 24, "Manage users & roles"), (60, 24, "View platform statistics"),
    ]
    for (x, y, t) in cases:
        ell(ax, x, y, 34, 9, t, fs=7.6)
    # a few association lines
    arrow(ax, 9, 78, 24, 88, style="-", color="#9aa3b2")
    arrow(ax, 9, 76, 24, 76, style="-", color="#9aa3b2")
    arrow(ax, 9, 48, 24, 64, style="-", color="#9aa3b2")
    arrow(ax, 9, 46, 60, 52, style="-", color="#9aa3b2")
    arrow(ax, 9, 18, 60, 40, style="-", color="#9aa3b2")
    arrow(ax, 9, 16, 24, 28, style="-", color="#9aa3b2")
    save(fig, "fig4_4_usecase.png")


# ---------------------------------------------------------------- Fig 4.5
def er_diagram():
    fig, ax = _fig(10.5, 7.6)

    def coll(x, y, title, fields, h):
        box(ax, x, y, 26, 5, title, fc=PRIMARY, ec=PRIMARY, tc="white", bold=True, fs=9)
        box(ax, x, y - h, 26, h, "\n".join(fields), fc="white", ec=PRIMARY, fs=7.3)

    coll(4, 90, "users", ["_id (PK)", "name, email (uniq)", "password_hash", "phone, about", "role, created_at"], 26)
    coll(68, 90, "properties", ["_id (PK)", "owner_id (FK→users)", "title, listing_type", "price, area_sqft, city", "status, featured, views", "amenities[], images[]"], 30)
    coll(4, 34, "saved", ["_id (PK)", "user_id (FK→users)", "property_id (FK→prop)", "created_at"], 20)
    coll(40, 30, "enquiries", ["_id (PK)", "property_id (FK→prop)", "owner_id (FK→users)", "sender_id (FK→users)", "message, reply, status"], 26)
    coll(74, 30, "predictions", ["_id (PK)", "user_id (FK→users)", "features{}", "predicted_price", "created_at"], 24)
    # relations (clean, minimal crossing)
    arrow(ax, 30, 78, 68, 78, style="-|>", text="1  owns  N\n(owner_id)")   # users -> properties
    arrow(ax, 14, 64, 14, 34, style="-|>", text="1:N\n(user_id)")            # users -> saved
    arrow(ax, 27, 64, 48, 30, style="-|>", color="#8a93a6", text="owner/sender")  # users -> enquiries
    arrow(ax, 72, 60, 60, 30, style="-|>", color="#8a93a6", text="1:N\n(property_id)")  # properties -> enquiries
    arrow(ax, 68, 64, 30, 26, style="-|>", color="#c2c9d6")                  # properties -> saved
    arrow(ax, 28, 66, 80, 30, style="-|>", color="#c2c9d6", text="user_id")  # users -> predictions
    save(fig, "fig4_5_er.png")


# ---------------------------------------------------------------- Fig 4.6
def dfd0():
    fig, ax = _fig(10.5, 4.6)
    for (x, y, t) in [(2, 40, "User /\nOwner"), (80, 40, "Admin")]:
        box(ax, x, y, 18, 20, t, fc=FILL2, ec=ACCENT, bold=True)
    ax.add_patch(Ellipse((50, 50), 34, 30, fc=FILL, ec=PRIMARY, lw=1.6))
    ax.text(50, 50, "0\nNestQuest\nMarketplace", ha="center", va="center", fontsize=10, fontweight="bold", color=INK)
    arrow(ax, 20, 55, 33, 55, text="listings, enquiries")
    arrow(ax, 33, 45, 20, 45, text="results, prices")
    arrow(ax, 80, 50, 67, 50, text="moderation")
    arrow(ax, 67, 45, 80, 45, text="statistics")
    save(fig, "fig4_6_dfd0.png")


# ---------------------------------------------------------------- Fig 4.7
def dfd1():
    fig, ax = _fig(10.5, 7.2)
    box(ax, 2, 46, 15, 12, "User", fc=FILL2, ec=ACCENT, bold=True)
    procs = [(26, 80, "1.0 Authenticate"), (26, 60, "2.0 Manage Listings"),
             (26, 40, "3.0 Search & View"), (26, 20, "4.0 Enquiries"), (60, 10, "5.0 AI Estimate")]
    for (x, y, t) in procs:
        ax.add_patch(Ellipse((x + 9, y + 5), 26, 13, fc=FILL, ec=PRIMARY, lw=1.4))
        ax.text(x + 9, y + 5, t, ha="center", va="center", fontsize=8, color=INK)
    stores = [(62, 78, "D1 users"), (62, 58, "D2 properties"), (62, 38, "D3 saved / enquiries"), (86, 12, "D4 predictions")]
    for (x, y, t) in stores:
        box(ax, x, y, 22, 8, t, fc="white", ec=GREY, fs=8)
    for (_, py) in [(0, 85), (0, 65), (0, 45), (0, 25)]:
        arrow(ax, 17, 52, 26, py, color="#9aa3b2", style="-")
    arrow(ax, 52, 85, 62, 82)
    arrow(ax, 52, 65, 62, 62)
    arrow(ax, 52, 45, 62, 45)
    arrow(ax, 52, 25, 62, 42)
    arrow(ax, 78, 15, 86, 16, color=GREEN)
    save(fig, "fig4_7_dfd1.png")


# ---------------------------------------------------------------- Fig 4.8
def sequence():
    fig, ax = _fig(10.5, 7.4)
    lanes = [("Browser", 10), ("app.js", 28), ("FastAPI", 48), ("Cloudinary", 70), ("MongoDB", 90)]
    for (name, x) in lanes:
        box(ax, x - 8, 90, 16, 7, name, fc=FILL, ec=PRIMARY, bold=True, fs=8.5)
        ax.plot([x, x], [10, 90], color="#c5ccda", lw=1.2, ls="--")
    msgs = [
        (10, 28, 84, "fill form, pick images"),
        (28, 48, 78, "POST /post submit"),
        (48, 70, 72, "upload image bytes"),
        (70, 48, 66, "secure_url(s)"),
        (48, 48, 60, "validate (Pydantic)"),
        (48, 90, 54, "insert property doc"),
        (90, 48, 48, "inserted _id"),
        (48, 28, 42, "201 {property}"),
        (28, 10, 36, "redirect /property/{id}"),
    ]
    for (x1, x2, y, t) in msgs:
        if x1 == x2:
            ax.add_patch(FancyBboxPatch((x1, y - 2), 2.5, 4, boxstyle="square,pad=0.1", fc=ACCENT, ec=ACCENT))
            ax.text(x1 + 5, y, t, fontsize=7.3, color=INK, va="center")
        else:
            arrow(ax, x1, y, x2, y, color=(GREEN if "image" in t or "url" in t else GREY))
            ax.text((x1 + x2) / 2, y + 1.5, t, fontsize=7.3, color=INK, ha="center")
    save(fig, "fig4_8_sequence.png")


# ---------------------------------------------------------------- Fig 4.9
def flowchart():
    fig, ax = _fig(8.6, 9.2)

    def term(x, y, t, fc=FILL3, ec=GREEN):
        ax.add_patch(FancyBboxPatch((x, y), 30, 7, boxstyle="round,pad=0.3,rounding_size=3.5", fc=fc, ec=ec, lw=1.4))
        ax.text(x + 15, y + 3.5, t, ha="center", va="center", fontsize=8.5, color=INK)

    def proc(x, y, t):
        box(ax, x, y, 30, 7, t, fs=8.3)

    def dec(x, y, t):
        ax.add_patch(plt.Polygon([(x + 17, y + 11), (x + 34, y + 5.5), (x + 17, y), (x, y + 5.5)],
                                 closed=True, fc=FILL2, ec=ACCENT, lw=1.4))
        ax.text(x + 17, y + 5.5, t, ha="center", va="center", fontsize=7.8, color=INK)

    term(35, 90, "Start")
    proc(35, 80, "User opens /post")
    dec(33, 66, "Logged in?")
    proc(72, 67, "Redirect /login")
    proc(35, 55, "Fill form + add images")
    proc(35, 45, "Click Publish")
    proc(35, 35, "Upload images → Cloudinary")
    dec(33, 21, "Valid &\nuploaded?")
    proc(72, 22, "Show error")
    proc(35, 10, "Create listing in MongoDB")
    term(35, 0.5, "View listing / End")
    arrow(ax, 50, 90, 50, 87)
    arrow(ax, 50, 80, 50, 77)
    arrow(ax, 50, 66, 50, 62)
    arrow(ax, 67, 71, 72, 71, text="No")
    arrow(ax, 50, 55, 50, 52, text="Yes", color=GREEN)
    arrow(ax, 50, 45, 50, 42)
    arrow(ax, 50, 35, 50, 32)
    arrow(ax, 50, 21, 50, 17, text="Yes", color=GREEN)
    arrow(ax, 67, 26, 72, 26, text="No")
    arrow(ax, 87, 22, 87, 58)
    arrow(ax, 87, 58, 65, 58.5)
    arrow(ax, 50, 10, 50, 7.5)
    save(fig, "fig4_9_flowchart.png")


# ---------------------------------------------------------------- Fig 4.10
def deployment():
    fig, ax = _fig(10.5, 5.4)
    box(ax, 2, 38, 20, 22, "Client device\n«browser»\nHTML/CSS/JS", fc=FILL2, ec=ACCENT, bold=True, fs=8.5)
    box(ax, 32, 34, 28, 34, "Application Server «node»\nUvicorn + FastAPI\n(backend.main:app)\nJinja2 · routers · ML model.pkl",
        fc=FILL, ec=PRIMARY, bold=True, fs=8.5)
    box(ax, 70, 58, 28, 12, "MongoDB Atlas\n«cloud database»", fc=FILL3, ec=GREEN, bold=True, fs=8.5)
    box(ax, 70, 40, 28, 12, "Cloudinary\n«media CDN»", fc=FILL3, ec=GREEN, fs=8.5)
    box(ax, 70, 22, 28, 12, "SMTP server\n«email, optional»", fc=FILL3, ec=GREEN, fs=8.5)
    arrow(ax, 22, 50, 32, 51, style="<|-|>", text="HTTPS")
    arrow(ax, 60, 58, 70, 63, style="<|-|>", text="TLS/Motor")
    arrow(ax, 60, 50, 70, 46, style="<|-|>", color=GREEN, text="REST")
    arrow(ax, 60, 42, 70, 28, style="-|>", color=GREEN)
    save(fig, "fig4_10_deployment.png")


# ---------------------------------------------------------------- Fig 5.1 (module interaction)
def module_interaction():
    fig, ax = _fig(10.5, 6.0)
    box(ax, 40, 84, 20, 10, "main.py\n(app factory)", fc=PRIMARY, ec=PRIMARY, tc="white", bold=True, fs=9)
    mods = [(4, 60, "auth"), (24, 60, "properties"), (44, 60, "enquiries"),
            (64, 60, "admin"), (84, 60, "ml"), (4, 60, "")]
    for (x, y, t) in [(2, 62, "auth"), (20, 62, "properties"), (39, 62, "enquiries"),
                      (58, 62, "admin"), (76, 62, "ml"), (90, 62, "uploads")]:
        box(ax, x, y, 15, 9, t, fs=8)
        arrow(ax, 50, 84, x + 7, 71, color="#c5ccda")
    box(ax, 2, 40, 15, 9, "pages", fs=8)
    arrow(ax, 50, 84, 9, 49, color="#c5ccda")
    box(ax, 20, 38, 16, 10, "deps.py\nmodels.py", fs=8)
    box(ax, 42, 38, 16, 10, "database.py", fc=FILL, ec=PRIMARY, bold=True, fs=8)
    box(ax, 64, 38, 16, 10, "security.py\nutils.py", fs=8)
    box(ax, 84, 38, 14, 10, "ml/predict", fc=FILL3, ec=GREEN, fs=8)
    for x in (10, 27, 45, 65, 83, 91):
        arrow(ax, x, 62, x if x < 50 else 50, 48, color="#dfe4ee", style="-")
    box(ax, 30, 18, 18, 9, "MongoDB Atlas", fc=FILL3, ec=GREEN, bold=True, fs=8)
    box(ax, 56, 18, 18, 9, "Cloudinary / SMTP", fc=FILL3, ec=GREEN, fs=8)
    arrow(ax, 50, 38, 39, 27, color=GREEN)
    arrow(ax, 72, 38, 65, 27, color=GREEN)
    save(fig, "fig5_1_modules.png")


if __name__ == "__main__":
    existing_workflow()
    proposed_workflow()
    architecture()
    block_diagram()
    component_interaction()
    use_case()
    er_diagram()
    dfd0()
    dfd1()
    sequence()
    flowchart()
    deployment()
    module_interaction()
    print("All figures generated in", OUT)
