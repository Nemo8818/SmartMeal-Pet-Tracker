"""Small, self-contained SVG illustrations for the SmartMeal pet room."""

from __future__ import annotations

import base64
from html import escape
import re
from xml.etree import ElementTree


PET_COLORS = {
    "cat": ("#f3b894", "#d98261", "#fff1df", "#c96f7f"),
    "rabbit": ("#ead8ef", "#c5a8d0", "#fff9ff", "#d986a1"),
    "dog": ("#efd1a6", "#c39162", "#fff5e4", "#bd7180"),
    "bear": ("#c9946e", "#936347", "#f4dec8", "#a95e69"),
    "penguin": ("#47596f", "#26384d", "#fffaf1", "#f0a24c"),
}


def svg_data_uri(svg: str) -> str:
    """Validate a complete SVG and return a browser-ready base64 data URI."""
    document = svg.strip()
    try:
        root = ElementTree.fromstring(document)
    except ElementTree.ParseError as error:
        raise ValueError("The illustration is not valid SVG/XML.") from error

    svg_tag = "{http://www.w3.org/2000/svg}svg"
    if root.tag != svg_tag or not root.get("viewBox"):
        raise ValueError("SVG illustrations need the SVG namespace and a viewBox.")
    if any(node.tag == svg_tag and not node.get("viewBox") for node in root.iter()):
        raise ValueError("Every nested SVG illustration needs a viewBox.")

    encoded = base64.b64encode(document.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "-", value)
    return cleaned or "smartmeal"


def _pet_features(kind: str, prefix: str, stage: str) -> str:
    """Return the animal shapes, with stage-specific growth and accessories."""
    body, shade, belly, accent = PET_COLORS[kind]
    size = {"Baby": 0.76, "Child": 0.88, "Teen": 0.98, "Adult": 1.04}.get(
        stage, 1.0
    )
    ears = {
        "cat": (
            f'<path d="M70 88 78 42 111 72 130 72 162 43 170 91Z" '
            f'fill="url(#{prefix}-body)" stroke="{shade}" stroke-width="3"/>'
        ),
        "rabbit": (
            f'<ellipse cx="87" cy="63" rx="19" ry="48" transform="rotate(-12 87 63)" '
            f'fill="url(#{prefix}-body)"/><ellipse cx="153" cy="63" rx="19" ry="48" '
            f'transform="rotate(12 153 63)" fill="url(#{prefix}-body)"/>'
            f'<ellipse cx="87" cy="63" rx="8" ry="34" transform="rotate(-12 87 63)" '
            f'fill="#f1b8c8"/><ellipse cx="153" cy="63" rx="8" ry="34" '
            f'transform="rotate(12 153 63)" fill="#f1b8c8"/>'
        ),
        "dog": (
            f'<ellipse cx="66" cy="103" rx="20" ry="39" transform="rotate(24 66 103)" '
            f'fill="url(#{prefix}-shade)"/><ellipse cx="174" cy="103" rx="20" ry="39" '
            f'transform="rotate(-24 174 103)" fill="url(#{prefix}-shade)"/>'
        ),
        "bear": (
            f'<circle cx="76" cy="75" r="26" fill="url(#{prefix}-body)"/>'
            f'<circle cx="164" cy="75" r="26" fill="url(#{prefix}-body)"/>'
            f'<circle cx="76" cy="75" r="13" fill="{belly}"/>'
            f'<circle cx="164" cy="75" r="13" fill="{belly}"/>'
        ),
        "penguin": (
            f'<path d="M91 57 Q120 30 149 57" fill="none" stroke="{shade}" '
            'stroke-width="8" stroke-linecap="round"/>'
        ),
    }[kind]

    if kind == "penguin":
        muzzle = (
            f'<path d="M108 123 Q120 112 132 123 L120 137Z" '
            f'fill="{accent}" stroke="#d68736" stroke-width="2"/>'
        )
        belly_shape = (
            f'<ellipse cx="120" cy="160" rx="36" ry="45" fill="{belly}" '
            'stroke="#e8e1d6" stroke-width="2"/>'
        )
    elif kind == "dog":
        muzzle = (
            f'<ellipse cx="120" cy="130" rx="24" ry="17" fill="{belly}"/>'
            f'<ellipse cx="120" cy="123" rx="7" ry="5" fill="{accent}"/>'
            '<path d="M120 128v7m0 0q-8 8-13 1m13-1q8 8 13 1" fill="none" '
            'stroke="#6e4e4c" stroke-width="2.8" stroke-linecap="round"/>'
        )
        belly_shape = (
            f'<ellipse cx="120" cy="162" rx="35" ry="32" fill="{belly}" '
            'opacity=".92"/>'
        )
    elif kind == "bear":
        muzzle = (
            f'<ellipse cx="120" cy="130" rx="22" ry="17" fill="{belly}"/>'
            f'<ellipse cx="120" cy="124" rx="7" ry="5" fill="{accent}"/>'
            '<path d="M120 129v6m0 0q-8 7-13 1m13-1q8 7 13 1" fill="none" '
            'stroke="#6e4e4c" stroke-width="2.8" stroke-linecap="round"/>'
        )
        belly_shape = (
            f'<ellipse cx="120" cy="161" rx="35" ry="33" fill="{belly}" '
            'opacity=".95"/>'
        )
    elif kind == "rabbit":
        muzzle = (
            f'<ellipse cx="120" cy="130" rx="22" ry="16" fill="{belly}"/>'
            f'<path d="M115 127q5-5 10 0-5 9-10 0" fill="{accent}"/>'
            '<path d="M120 132v5m0 0q-7 6-12 1m12-1q7 6 12 1" fill="none" '
            'stroke="#76556a" stroke-width="2.6" stroke-linecap="round"/>'
        )
        belly_shape = (
            f'<ellipse cx="120" cy="161" rx="35" ry="33" fill="{belly}" '
            'opacity=".95"/>'
        )
    else:
        muzzle = (
            f'<path d="M114 126q6-7 12 0-6 10-12 0" fill="{accent}"/>'
            '<path d="M120 132v5m0 0q-7 6-12 1m12-1q7 6 12 1" fill="none" '
            'stroke="#76545a" stroke-width="2.6" stroke-linecap="round"/>'
        )
        belly_shape = (
            f'<ellipse cx="120" cy="161" rx="34" ry="32" fill="{belly}" '
            'opacity=".94"/>'
        )

    cheeks = (
        '<ellipse cx="88" cy="123" rx="11" ry="7" fill="#ee9ba7" opacity=".55"/>'
        '<ellipse cx="152" cy="123" rx="11" ry="7" fill="#ee9ba7" opacity=".55"/>'
    )
    whiskers = ""
    if kind == "cat":
        whiskers = (
            '<path d="m91 130-22-4m22 10-23 5m61-11 22-4m-22 10 23 5" '
            'stroke="#b87668" stroke-width="2" stroke-linecap="round" opacity=".7"/>'
        )

    accessory = ""
    if stage == "Teen":
        accessory = (
            '<path d="M76 75 Q120 47 164 75" fill="none" stroke="#8d78bb" '
            'stroke-width="8" stroke-linecap="round"/>'
            '<path d="m164 64 4 8 9 1-7 6 2 9-8-5-8 5 2-9-7-6 9-1Z" '
            'fill="#f7ce70" stroke="#e6aa58" stroke-width="1.5"/>'
        )
    elif stage == "Adult":
        accessory = (
            '<path d="M74 166 Q120 184 166 166 L162 180 Q120 198 78 180Z" '
            'fill="#b987c9" stroke="#9b70af" stroke-width="2"/>'
            '<circle cx="120" cy="184" r="7" fill="#f6d77c"/>'
        )

    if kind == "penguin":
        wings = (
            f'<ellipse cx="65" cy="156" rx="16" ry="39" transform="rotate(18 65 156)" '
            f'fill="url(#{prefix}-shade)"/>'
            f'<ellipse cx="175" cy="156" rx="16" ry="39" transform="rotate(-18 175 156)" '
            f'fill="url(#{prefix}-shade)"/>'
        )
    else:
        wings = ""

    scale_group = (
        '<g transform="translate(120 128) scale('
        f"{size}) translate(-120 -128)"
        '">'
    )
    return (
        scale_group
        + '<ellipse cx="120" cy="210" rx="55" ry="11" fill="#765e72" opacity=".16"/>'
        + f'<ellipse cx="88" cy="191" rx="20" ry="14" fill="url(#{prefix}-body)"/>'
        + f'<ellipse cx="152" cy="191" rx="20" ry="14" fill="url(#{prefix}-body)"/>'
        + f'<ellipse cx="120" cy="164" rx="56" ry="50" fill="url(#{prefix}-body)" '
        f'filter="url(#{prefix}-shadow)"/>'
        + wings
        + belly_shape
        + ears
        + f'<circle cx="120" cy="102" r="57" fill="url(#{prefix}-body)" '
        f'stroke="rgba(120,80,90,.12)" stroke-width="2" filter="url(#{prefix}-shadow)"/>'
        + '<ellipse cx="99" cy="73" rx="19" ry="9" transform="rotate(-24 99 73)" '
        'fill="white" opacity=".32"/>'
        + '<ellipse cx="101" cy="105" rx="6" ry="9" fill="#3e3540"/>'
        + '<ellipse cx="139" cy="105" rx="6" ry="9" fill="#3e3540"/>'
        + '<circle cx="103" cy="102" r="2.3" fill="white"/>'
        + '<circle cx="141" cy="102" r="2.3" fill="white"/>'
        + cheeks
        + muzzle
        + whiskers
        + accessory
        + "</g>"
    )


def pet_svg(
    kind: str,
    stage: str,
    *,
    instance_id: str = "pet",
    x: int | None = None,
    y: int | None = None,
    width: int = 240,
    height: int = 240,
) -> str:
    """Draw the mystery egg or a softly shaded, round animal character."""
    prefix = _safe_id(instance_id)
    placement = (
        f'x="{x}" y="{y}" width="{width}" height="{height}"'
        if x is not None and y is not None
        else f'width="{width}" height="{height}" style="max-width:100%;height:auto;display:block;margin:auto"'
    )
    if stage == "Egg":
        character = (
            '<ellipse cx="120" cy="205" rx="52" ry="10" fill="#765e72" opacity=".14"/>'
            f'<path d="M120 45 C88 45 64 108 67 151 C70 187 92 202 120 202 '
            'C148 202 170 187 173 151 C176 108 152 45 120 45Z" '
            f'fill="url(#{prefix}-egg)" stroke="#e1a8bd" stroke-width="3" '
            f'filter="url(#{prefix}-shadow)"/>'
            '<path d="M91 83q-8 17-10 34" fill="none" stroke="white" '
            'stroke-width="9" stroke-linecap="round" opacity=".58"/>'
            '<circle cx="145" cy="130" r="5" fill="#f8d274"/>'
            '<path d="m145 119 3 7 7 3-7 3-3 7-3-7-7-3 7-3Z" fill="#fff7dc"/>'
            '<circle cx="97" cy="155" r="4" fill="#dca2bd"/>'
        )
        label = "A soft pastel mystery egg"
    else:
        kind = kind if kind in PET_COLORS else "cat"
        character = _pet_features(kind, prefix, stage)
        label = f"A round {kind} pet at the {stage.lower()} stage"

    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"
         {placement} role="img" aria-label="{escape(label)}">
      <defs>
        <linearGradient id="{prefix}-body" x1="0" y1="0" x2=".85" y2="1">
          <stop offset="0" stop-color="{PET_COLORS.get(kind, PET_COLORS['cat'])[0] if stage != 'Egg' else '#fff4db'}"/>
          <stop offset=".55" stop-color="{PET_COLORS.get(kind, PET_COLORS['cat'])[0] if stage != 'Egg' else '#f6c8d6'}"/>
          <stop offset="1" stop-color="{PET_COLORS.get(kind, PET_COLORS['cat'])[1] if stage != 'Egg' else '#eaa8c1'}"/>
        </linearGradient>
        <linearGradient id="{prefix}-shade" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="{PET_COLORS.get(kind, PET_COLORS['cat'])[0] if stage != 'Egg' else '#f7ccda'}"/>
          <stop offset="1" stop-color="{PET_COLORS.get(kind, PET_COLORS['cat'])[1] if stage != 'Egg' else '#d98cae'}"/>
        </linearGradient>
        <linearGradient id="{prefix}-egg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#fff5df"/>
          <stop offset=".55" stop-color="#f8d8e4"/>
          <stop offset="1" stop-color="#e9b8d5"/>
        </linearGradient>
        <filter id="{prefix}-shadow" x="-30%" y="-30%" width="160%" height="170%">
          <feDropShadow dx="0" dy="7" stdDeviation="7" flood-color="#70566d" flood-opacity=".16"/>
        </filter>
      </defs>
      {character}
    </svg>
    """


def room_svg(kind: str, stage: str, decor_items: set[str] | list[str] | tuple[str, ...]) -> str:
    """Build the cozy bedroom scene and place the current pet in it."""
    items = set(decor_items)
    wall = "#f6e5f1" if "lavender_wallpaper" in items else "#f9e6e8"
    rug = "#d8c6eb" if "moon_rug" in items else "#f3d0d8"
    stars = (
        '<path d="m395 73 5 10 11 2-8 7 2 11-10-5-10 5 2-11-8-7 11-2Z" '
        'fill="#fff5c9"/><path d="m474 111 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z" '
        'fill="#fff5c9"/><circle cx="527" cy="67" r="4" fill="#fff5c9"/>'
        if "star_wallpaper" in items
        else ""
    )
    fairy_lights = (
        '<path d="M320 34q50 48 100 0t100 0 100 0" fill="none" '
        'stroke="#c38e9c" stroke-width="3"/>'
        + "".join(
            f'<circle cx="{x}" cy="{y}" r="6" fill="#f8d779" stroke="#fff4c2" stroke-width="3"/>'
            for x, y in [(337, 48), (379, 55), (420, 35), (462, 48), (505, 55), (548, 38), (590, 50)]
        )
        if "fairy_lights" in items
        else ""
    )
    plant_flower = (
        '<circle cx="105" cy="267" r="11" fill="#f3c76a"/>'
        '<circle cx="105" cy="250" r="8" fill="#f4a4ac"/>'
        '<circle cx="121" cy="260" r="8" fill="#f4a4ac"/>'
        '<circle cx="99" cy="277" r="8" fill="#f4a4ac"/>'
        '<circle cx="89" cy="260" r="8" fill="#f4a4ac"/>'
        if "sunflower_plant" in items
        else ""
    )
    extra_plant = (
        '<path d="M750 356v-70m0 39q-30-4-34-31 25-6 34 31m0-16q29-7 31-31-24-3-31 31" '
        'fill="#8fc3a0" stroke="#5f9a78" stroke-width="3"/>'
        '<path d="M728 355h44l-5 31h-34Z" fill="#e8a6ac" stroke="#c88091" stroke-width="3"/>'
        if "sprout_planter" in items
        else ""
    )
    lamp = (
        '<path d="M807 217h43l-7 26h-29Z" fill="#f6dc94" stroke="#dbbb72" stroke-width="3"/>'
        '<path d="M828 243v27" stroke="#a98273" stroke-width="5"/>'
        '<path d="M813 272h31" stroke="#a98273" stroke-width="6" stroke-linecap="round"/>'
        '<path d="M828 218v-9" stroke="#a98273" stroke-width="4"/>'
        if "cloud_lamp" in items
        else ""
    )
    bookshelf = (
        '<rect x="775" y="82" width="99" height="122" rx="8" fill="#c99575" stroke="#ab765f" stroke-width="4"/>'
        '<path d="M775 123h99m-99 40h99" stroke="#ab765f" stroke-width="4"/>'
        '<rect x="787" y="92" width="12" height="27" rx="3" fill="#e5aab4"/>'
        '<rect x="804" y="87" width="12" height="32" rx="3" fill="#a8cdb5"/>'
        '<rect x="821" y="98" width="12" height="21" rx="3" fill="#b9a3d7"/>'
        '<rect x="840" y="91" width="12" height="28" rx="3" fill="#f1cf86"/>'
        '<rect x="787" y="132" width="12" height="26" rx="3" fill="#a8cdb5"/>'
        '<rect x="805" y="137" width="12" height="21" rx="3" fill="#e5aab4"/>'
        '<rect x="823" y="129" width="12" height="29" rx="3" fill="#f1cf86"/>'
        if "bookshelf" in items
        else ""
    )
    toy = (
        '<circle cx="316" cy="410" r="24" fill="#f6c86f" stroke="#e7ad52" stroke-width="3"/>'
        '<path d="M298 399q18 21 36 0m-36 22q18-21 36 0" fill="none" stroke="#fff0c5" stroke-width="4"/>'
        if "yarn_ball" in items
        else ""
    )
    plush = (
        '<circle cx="581" cy="405" r="19" fill="#ead5ec" stroke="#c4a4cb" stroke-width="3"/>'
        '<circle cx="567" cy="390" r="8" fill="#ead5ec"/><circle cx="595" cy="390" r="8" fill="#ead5ec"/>'
        '<circle cx="575" cy="404" r="2" fill="#554b5a"/><circle cx="587" cy="404" r="2" fill="#554b5a"/>'
        '<path d="M579 411q4 4 8 0" fill="none" stroke="#b4778e" stroke-width="2"/>'
        if "plush_bunny" in items
        else ""
    )
    flower_rug = (
        '<circle cx="438" cy="455" r="13" fill="#fff3d2"/>'
        '<circle cx="438" cy="435" r="11" fill="#fff9e7"/>'
        '<circle cx="457" cy="455" r="11" fill="#fff9e7"/>'
        '<circle cx="438" cy="475" r="11" fill="#fff9e7"/>'
        '<circle cx="419" cy="455" r="11" fill="#fff9e7"/>'
        if "flower_rug" in items
        else ""
    )
    pet = pet_svg(
        kind,
        stage,
        instance_id="room-pet",
        x=348,
        y=243,
        width=218,
        height=218,
    )
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 520"
         role="img" aria-label="Cozy pastel pet bedroom with a soft bed, window, rug, plant and toys"
         style="width:100%;height:auto;display:block">
      <defs>
        <linearGradient id="room-wall" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="{wall}"/><stop offset="1" stop-color="#fdf3e9"/>
        </linearGradient>
        <linearGradient id="room-floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#edcfb2"/><stop offset="1" stop-color="#d9b696"/>
        </linearGradient>
        <linearGradient id="room-bed" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#f5d2d6"/><stop offset="1" stop-color="#d89cae"/>
        </linearGradient>
        <filter id="room-shadow" x="-20%" y="-20%" width="140%" height="150%">
          <feDropShadow dx="0" dy="7" stdDeviation="7" flood-color="#8e6d77" flood-opacity=".15"/>
        </filter>
      </defs>
      <rect width="920" height="520" rx="28" fill="url(#room-wall)"/>
      {stars}{fairy_lights}
      <path d="M0 344h920v176H0Z" fill="url(#room-floor)"/>
      <path d="M0 346h920" stroke="#c99e86" stroke-width="7"/>
      <path d="M0 414h920M0 478h920" stroke="#c89f82" stroke-width="2" opacity=".4"/>
      <path d="M175 346v174m188-174v174m188-174v174m188-174v174" stroke="#c89f82" stroke-width="2" opacity=".3"/>

      <g filter="url(#room-shadow)">
        <rect x="70" y="64" width="218" height="205" rx="20" fill="#fffaf4" stroke="#d4aab4" stroke-width="9"/>
        <rect x="84" y="78" width="190" height="177" rx="12" fill="#bfe0e3"/>
        <path d="M84 194q41-42 82-6t108-13v80H84Z" fill="#a8cdb7" opacity=".9"/>
        <circle cx="226" cy="116" r="22" fill="#ffe8a7"/>
        <path d="M179 78v177m-95-88h190" stroke="#fffaf4" stroke-width="11"/>
        <path d="M58 65q25 30 19 110t-7 98h28V64Zm242 0q-25 30-19 110t7 98h-28V64Z" fill="#dfa9bd" opacity=".9"/>
        <path d="M65 65q26 25 40 0m163 0q20 24 37 0" fill="none" stroke="#c587a2" stroke-width="7"/>
      </g>
      <path d="M381 139q13-18 26 0 13-18 26 0" fill="none" stroke="#c191a5" stroke-width="5" stroke-linecap="round"/>
      <circle cx="393" cy="156" r="4" fill="#f0b960"/><circle cx="421" cy="156" r="4" fill="#f0b960"/>

      <g>
        <path d="M93 337q-8-47 13-75 18 21 6 56 17-53 42-60 10 29-19 62 29-42 55-37 1 31-37 57Z"
              fill="#8db89a" stroke="#6e9d7d" stroke-width="3"/>
        {plant_flower}
        <path d="M93 335h102l-13 53H107Z" fill="#db9ca2" stroke="#bb7883" stroke-width="4"/>
        <path d="M85 334h118v13H85Z" rx="5" fill="#efb8b5"/>
      </g>
      {extra_plant}

      <g filter="url(#room-shadow)">
        <rect x="550" y="208" width="226" height="156" rx="23" fill="#bd886c" stroke="#a86f5e" stroke-width="5"/>
        <rect x="569" y="190" width="188" height="135" rx="24" fill="url(#room-bed)" stroke="#d18e9f" stroke-width="4"/>
        <path d="M583 271q54-34 113 0t48 0v57H583Z" fill="#edc1d0"/>
        <path d="M590 224q35-22 67 0v29h-67Z" fill="#fff8ef" stroke="#e8d5d4" stroke-width="3"/>
        <path d="M664 224q35-22 67 0v29h-67Z" fill="#fff8ef" stroke="#e8d5d4" stroke-width="3"/>
        <path d="M555 352v36m213-36v36" stroke="#a86f5e" stroke-width="12" stroke-linecap="round"/>
        <path d="M545 389h235" stroke="#a86f5e" stroke-width="10" stroke-linecap="round"/>
      </g>
      <ellipse cx="458" cy="465" rx="226" ry="43" fill="{rug}" opacity=".92"/>
      <ellipse cx="458" cy="465" rx="195" ry="30" fill="none" stroke="#fff7ec" stroke-width="5" opacity=".9"/>
      {flower_rug}

      <g>
        <rect x="789" y="267" width="83" height="53" rx="8" fill="#c89175" stroke="#a8735d" stroke-width="4"/>
        <path d="M799 321v34m63-34v34" stroke="#a8735d" stroke-width="7"/>
        {lamp}
      </g>
      {bookshelf}
      {toy}{plush}
      <g>
        <rect x="297" y="314" width="69" height="52" rx="12" fill="#fff0c9" stroke="#e6c789" stroke-width="4"/>
        <path d="M309 314v-16m22 16v-16m22 16v-16" stroke="#d89b79" stroke-width="5" stroke-linecap="round"/>
        <circle cx="322" cy="340" r="6" fill="#e4a4b0"/><circle cx="342" cy="340" r="6" fill="#9fc9b0"/>
      </g>
      {pet}
      <text x="44" y="493" fill="#8c697e" font-family="sans-serif" font-size="17" font-weight="600">
        a cozy little room
      </text>
    </svg>
    """
