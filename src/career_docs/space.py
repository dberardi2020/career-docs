"""The layout design space: enumerate it, measure it, name it.

The space is finite, deterministic, and a product of independent categorical axes,
which is the property everything else here leans on. It means the space can simply
be *enumerated* and browsed with the axes as facets — "every layout in this palette",
"this layout in any palette but this one" — so there is no recommender, no sampling
seed, and no session state to keep. A catalogue answers what a search engine would.

Distance is therefore Hamming: the number of axes on which two specs disagree,
0-7.
Crude, but it matches how the choices behave — swapping a palette changes exactly one
thing, and the metric should say exactly that. It underwrites `spread` (show me the
range), `neighbours` (show me the near-misses), and the merge of two specs, which is
just the sub-space they span.

Kept free of rendering and IO, so it can be reasoned about and tested on its own.
"""
from __future__ import annotations

import hashlib
from dataclasses import replace

from .compose import (DENSITIES, GROUPINGS, HEADERS, PALETTES, PROMOS, SKILLS,
                      TYPEFACES, Spec)

# Every axis, as (attribute, values). Order is stable so `axis_values` and
# distance stay consistent across runs.
AXES: list[tuple[str, list]] = [
    ("palette", list(range(len(PALETTES)))),
    ("typeface", list(range(len(TYPEFACES)))),
    ("header", list(HEADERS)),
    ("skills", list(SKILLS)),
    ("promo", list(PROMOS)),
    ("density", list(range(len(DENSITIES)))),
    ("grouping", list(GROUPINGS)),
]

TOTAL = 1
for _, _values in AXES:
    TOTAL *= len(_values)


def distance(a: Spec, b: Spec) -> int:
    """Number of axes on which two specs differ (0 = identical, 6 = nothing shared)."""
    return sum(1 for attr, _ in AXES if getattr(a, attr) != getattr(b, attr))


def neighbours(spec: Spec, radius: int = 1) -> list[Spec]:
    """Every spec within `radius` axis-changes of `spec`, excluding itself."""
    out: set[Spec] = set()
    frontier = {spec}
    for _ in range(max(1, radius)):
        nxt: set[Spec] = set()
        for current in frontier:
            for attr, values in AXES:
                for value in values:
                    if value == getattr(current, attr):
                        continue
                    nxt.add(replace(current, **{attr: value}))
        out |= nxt
        frontier = nxt
    out.discard(spec)
    return sorted(out, key=lambda s: s.name)


def spread(count: int) -> list[Spec]:
    """`count` layouts spread across the space, by greedy farthest-point selection.

    Taking the first N in enumeration order would return N near-identical layouts,
    since enumeration varies the last axis fastest. Farthest-point picks each next
    spec to maximise its minimum distance from those already chosen, so a handful
    of cards actually shows you the range of what the space can do.

    Deterministic: no seed, no shuffle. The same count always yields the same
    layouts, so a catalogue can be rebuilt, linked and compared.
    """
    pool = _all()
    if not pool or count <= 0:
        return []
    if count >= len(pool):
        return pool

    # `nearest[i]` is the distance from pool[i] to the closest spec already
    # chosen, updated incrementally as each pick lands. Recomputing it from
    # scratch each round instead would make this cubic in the size of the space,
    # which at ten thousand points does not finish.
    chosen = [pool[0]]
    taken = {0}
    nearest = [distance(cand, pool[0]) for cand in pool]

    while len(chosen) < count:
        best_i, best_score = -1, -1
        for i, score in enumerate(nearest):
            if i not in taken and score > best_score:
                best_i, best_score = i, score
        chosen.append(pool[best_i])
        taken.add(best_i)
        for i, cand in enumerate(pool):
            d = distance(cand, pool[best_i])
            if d < nearest[i]:
                nearest[i] = d
    return chosen


def _all() -> list[Spec]:
    from .compose import all_specs
    return all_specs()


# Value -> index, for the axes stored as indices into a table of tuples.
_PALETTE_IDS = {p[0]: i for i, p in enumerate(PALETTES)}
_TYPEFACE_IDS = {t[0]: i for i, t in enumerate(TYPEFACES)}
_DENSITY_IDS = {d[0]: i for i, d in enumerate(DENSITIES)}


def parse(name: str) -> Spec | None:
    """Recover a Spec from its name. Returns None if it does not parse.

    Decoded directly rather than by scanning the whole space for a match: the
    name spells out every axis, so it is a lookup per segment.
    """
    parts = name.split("-")
    if len(parts) != 7:
        return None
    palette, typeface, header, skills, promo, density, grouping = parts
    if (palette not in _PALETTE_IDS or typeface not in _TYPEFACE_IDS
            or density not in _DENSITY_IDS or header not in HEADERS
            or skills not in SKILLS or promo not in PROMOS
            or grouping not in GROUPINGS):
        return None
    return Spec(
        palette=_PALETTE_IDS[palette],
        typeface=_TYPEFACE_IDS[typeface],
        header=header,
        skills=skills,
        promo=promo,
        density=_DENSITY_IDS[density],
        grouping=grouping,
    )


# Browsing order, computed once. Enumeration order groups near-identical layouts
# together (the last axis varies fastest), so paging through it would show seven
# shades of one design per page. Ordering by a hash of the name mixes the space
# thoroughly while staying completely deterministic: page 3 is always page 3, on
# every machine, with no seed to carry and no state to store.
_ORDER: list[Spec] | None = None


def browse_order() -> list[Spec]:
    """Every spec, in a stable, well-mixed order."""
    global _ORDER
    if _ORDER is None:
        _ORDER = sorted(
            _all(),
            key=lambda s: hashlib.blake2b(s.name.encode(), digest_size=8).digest(),
        )
    return _ORDER


def _axis_value(spec: Spec, axis: str) -> str:
    """The spec's value on one axis, as the string a filter compares against — the
    same strings the chips and spec name use."""
    if axis == "palette":
        return PALETTES[spec.palette][0]
    if axis == "typeface":
        return TYPEFACES[spec.typeface][0]
    if axis == "density":
        return DENSITIES[spec.density][0]
    return getattr(spec, axis)  # header, skills, promo, grouping are stored as strings


# The filterable values of every axis, as the strings that appear in spec names,
# on the cards' chips and in a filter. `AXES` stores palette/typeface/density as
# indices into their tables, so it cannot answer this on its own — and the viewer,
# the server's query validation and the tests all need the same list.
AXIS_VALUES: dict[str, list[str]] = {
    "palette": [p[0] for p in PALETTES],
    "typeface": [t[0] for t in TYPEFACES],
    "header": list(HEADERS),
    "skills": list(SKILLS),
    "promo": list(PROMOS),
    "density": [d[0] for d in DENSITIES],
    "grouping": list(GROUPINGS),
}


def axis_values(axis: str) -> list[str]:
    """The values one axis can be filtered to. Empty for an unknown axis."""
    return AXIS_VALUES.get(axis, [])


Filter = str | list[str] | tuple[str, ...] | set[str]


def _active(filters: dict[str, Filter] | None) -> bool:
    """True if any axis is actually constrained. A dict of empty sets is not a
    filter — the viewer leaves emptied axes in place rather than deleting keys."""
    return bool(filters) and any(bool(v) for v in filters.values())


def matches(spec: Spec, filters: dict[str, Filter]) -> bool:
    """True if the spec satisfies every filtered axis.

    An axis may be constrained to one value or to several: several is an OR
    (`palette in {moss, plum}`), and axes combine with AND. A single string is
    the same thing with one member, so a one-value filter and the old scalar
    form mean exactly the same query.

    An empty collection means *unconstrained*, not *matches nothing* — the
    viewer clears an axis by emptying it, and an empty set narrowing the browse
    to zero results would make "clear" look like "no layouts found".
    """
    for axis, wanted in filters.items():
        if not wanted:          # empty string / list / set: this axis is unconstrained
            continue
        value = _axis_value(spec, axis)
        if isinstance(wanted, str):
            if value != wanted:
                return False
        elif wanted and value not in wanted:
            return False
    return True


def _order(filters: dict[str, Filter] | None) -> list[Spec]:
    """Browse order, narrowed to the specs that match every filter. Filtering is a
    view over the enumeration, not a separate space — holding an axis constant just
    hides the rest, which is what makes 'hold this colour/type' shrink the browse
    instead of paging the same layout in seven shades."""
    order = browse_order()
    if not _active(filters):
        return order
    return [s for s in order if matches(s, filters)]


def total(filters: dict[str, Filter] | None = None) -> int:
    """How many layouts are in the (optionally filtered) browse set."""
    return TOTAL if not _active(filters) else len(_order(filters))


def pages(count: int, filters: dict[str, Filter] | None = None) -> int:
    """How many pages of `count` the (optionally filtered) space divides into."""
    if count <= 0:
        return 0
    return -(-total(filters) // count)


def page(index: int, count: int, filters: dict[str, Filter] | None = None) -> list[Spec]:
    """One page of `count` layouts from the (optionally filtered) space. Wraps, so
    any index is valid."""
    if count <= 0:
        return []
    order = _order(filters)
    total_pages = pages(count, filters)
    if total_pages == 0:
        return []
    start = (index % total_pages) * count
    return order[start:start + count]
