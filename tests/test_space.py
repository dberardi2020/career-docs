"""The design space: enumeration, naming, distance, and the spread.

The naming tests carry the most weight here. A spec name is what gets saved,
linked and published against, so the properties that matter are that every spec
has a distinct name and that every name decodes back to the spec it came from —
for every one of them, not a sample. The previous scheme packed three axes into positional
digits and silently broke both promises whenever an axis gained a value; these
tests are what stop that returning.
"""
from __future__ import annotations

import pytest

from career_docs import compose, space

ALL = compose.all_specs()


def test_space_is_the_product_of_its_axes():
    expected = 1
    for _, values in space.AXES:
        expected *= len(values)
    assert space.TOTAL == expected == len(ALL) == 10080


def test_every_spec_is_enumerated_once():
    assert len(set(ALL)) == len(ALL)


def test_names_are_unique_across_the_whole_space():
    names = [s.name for s in ALL]
    assert len(set(names)) == len(names)


def test_every_name_round_trips():
    for spec in ALL:
        assert space.parse(spec.name) == spec


def test_name_spells_out_every_axis_in_order():
    spec = compose.Spec(palette=0, typeface=0, header="band",
                        skills="pills", promo="ladder", density=0)
    assert spec.name == "harbor-grotesk-band-pills-ladder-airy-grouped"
    assert spec.name.split("-") == [
        compose.PALETTES[0][0], compose.TYPEFACES[0][0],
        "band", "pills", "ladder", compose.DENSITIES[0][0], "grouped",
    ]


@pytest.mark.parametrize("bad", [
    "",
    "nope",
    "harbor",
    "a-b-c-d-e-f-g",                            # right shape, wrong values
    "harbor-grotesk-band-pills-ladder-airy",    # too few segments
    "harbor-grotesk-band-pills-ladder-airy-grouped-x",  # too many
    "harbor-321-mixed-compact",                 # the retired scheme
    "HARBOR-grotesk-band-pills-ladder-airy-grouped",  # case matters
])
def test_parse_rejects_anything_that_is_not_a_name(bad):
    assert space.parse(bad) is None


def test_names_survive_a_new_axis_value():
    """The regression that motivated the rename.

    Adding a value to an axis must not change what an existing name means. Under
    the old index-encoded scheme, inserting a header renumbered thousands of
    names; a published spec quietly came to refer to a different layout.
    """
    spec = compose.Spec(0, 0, compose.HEADERS[-1], "pills", "ladder", 0)
    before = spec.name

    compose.HEADERS.insert(0, "invented")
    try:
        assert spec.name == before
        assert space.parse(before) == spec
    finally:
        compose.HEADERS.remove("invented")


# ── distance ──────────────────────────────────────────────────────────────────

def test_distance_is_zero_only_for_itself():
    spec = ALL[0]
    assert space.distance(spec, spec) == 0


def test_distance_counts_differing_axes():
    a = compose.Spec(0, 0, "band", "pills", "ladder", 0)
    b = compose.Spec(1, 0, "band", "pills", "ladder", 0)
    c = compose.Spec(1, 1, "band", "pills", "ladder", 0)
    assert space.distance(a, b) == 1
    assert space.distance(a, c) == 2


def test_distance_is_symmetric_and_bounded():
    a, b = ALL[0], ALL[-1]
    assert space.distance(a, b) == space.distance(b, a)
    assert 0 <= space.distance(a, b) <= len(space.AXES)


# ── neighbours ────────────────────────────────────────────────────────────────

def test_radius_one_neighbours_are_one_change_away():
    spec = ALL[0]
    near = space.neighbours(spec, radius=1)
    assert spec not in near
    assert all(space.distance(spec, n) == 1 for n in near)


def test_radius_one_neighbour_count_is_the_sum_of_alternatives():
    spec = ALL[0]
    expected = sum(len(values) - 1 for _, values in space.AXES)
    assert len(space.neighbours(spec, radius=1)) == expected


def test_neighbours_widen_with_radius():
    spec = ALL[0]
    assert len(space.neighbours(spec, 2)) > len(space.neighbours(spec, 1))
    assert all(space.distance(spec, n) <= 2 for n in space.neighbours(spec, 2))


# ── spread ────────────────────────────────────────────────────────────────────

def test_spread_returns_the_requested_count():
    assert len(space.spread(12)) == 12


def test_spread_is_deterministic():
    assert [s.name for s in space.spread(9)] == [s.name for s in space.spread(9)]


def test_spread_has_no_duplicates():
    picked = space.spread(40)
    assert len({s.name for s in picked}) == len(picked)


def test_spread_actually_spreads():
    """A spread of six should not be six shades of the same layout.

    Taking the first N in enumeration order would return specs differing only in
    the fastest-varying axis. Every pair here differs on at least two axes.
    """
    picked = space.spread(6)
    pairs = [(a, b) for i, a in enumerate(picked) for b in picked[i + 1:]]
    assert all(space.distance(a, b) >= 2 for a, b in pairs)


@pytest.mark.parametrize("count", [0, -1])
def test_spread_of_nothing_is_empty(count):
    assert space.spread(count) == []


def test_spread_cannot_exceed_the_space():
    assert len(space.spread(space.TOTAL + 50)) == space.TOTAL


# ── filtering: holding an axis narrows the browse set (RP-0033/0035) ────────────

PALETTE = compose.PALETTES[0][0]    # "harbor"
TYPEFACE = compose.TYPEFACES[0][0]  # "grotesk"


def test_no_filter_is_the_whole_space():
    assert space.total() == space.TOTAL
    assert space.total({}) == space.TOTAL
    assert space.page(3, 12, {}) == space.page(3, 12) == space.page(3, 12, None)


def test_holding_one_axis_divides_the_space_by_that_axis():
    # Every palette holds an equal share, so fixing one is TOTAL / #palettes.
    assert space.total({"palette": PALETTE}) == space.TOTAL // len(compose.PALETTES)
    assert space.total({"typeface": TYPEFACE}) == space.TOTAL // len(compose.TYPEFACES)


def test_holding_two_axes_divides_by_both():
    expected = space.TOTAL // (len(compose.PALETTES) * len(compose.TYPEFACES))
    assert space.total({"palette": PALETTE, "typeface": TYPEFACE}) == expected  # 360


def test_a_filtered_page_holds_only_matching_layouts():
    filters = {"palette": PALETTE, "typeface": TYPEFACE}
    for spec in space.page(0, 24, filters):
        assert compose.PALETTES[spec.palette][0] == PALETTE
        assert compose.TYPEFACES[spec.typeface][0] == TYPEFACE


def test_pages_and_total_follow_the_filter():
    filters = {"palette": PALETTE}
    total = space.total(filters)
    assert space.pages(24, filters) == -(-total // 24)           # ceil, over the subset
    assert space.pages(24, filters) < space.pages(24)            # fewer than the whole space


def test_filtered_paging_covers_the_subset_once():
    """Paging a filter reaches every matching layout, and no page repeats one."""
    filters = {"typeface": TYPEFACE}
    count = 24
    seen: list[str] = []
    for index in range(space.pages(count, filters)):
        seen += [s.name for s in space.page(index, count, filters)]
    matching = {s.name for s in ALL if compose.TYPEFACES[s.typeface][0] == TYPEFACE}
    assert set(seen) == matching
    assert len(seen) == len(matching)   # no repeats
