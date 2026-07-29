"""Define the bounded representative Phase 5 transition editing workload.

The accepted plain-line transition family produces one canonical Entry and
one canonical Exit record for each secondary track.  A one-secondary-track
pair is therefore the smallest complete multi-object workload for the
currently qualified family.  The distinct transition lengths make the two
development previews pointer-disambiguable; they are test inputs, not product
defaults or capacity evidence.
"""

import math

from tracktemplate import api


WORKLOAD_ID = (
    "phase5-qualified-plain-line-one-secondary-track-entry-exit-v1"
)
WORKLOAD_RATIONALE = (
    "One qualified plain-line template set with one secondary track "
    "produces exactly two canonical transition records, Entry and Exit. "
    "The pair is the smallest complete multi-object workload for that "
    "currently qualified family."
)
WORKLOAD_SCOPE_LIMIT = (
    "Representative of the qualified fixture-only family shape, not a "
    "whole-layout capacity, renderer-suitability or interaction budget."
)
TEMPLATE_SET_ID = "SET-001"
TRACK_NUMBER = 2
OBJECT_COUNT = 2
PREVIEW_SEGMENT_COUNT = 32
ENTRY_TRANSITION_LENGTH_MM = 300.0
EXIT_TRANSITION_LENGTH_MM = 420.0
EDITED_EXIT_TRANSITION_LENGTH_MM = 360.0
FAILED_EXIT_TRANSITION_LENGTH_MM = 390.0


def _transition_id(end_name):
    return "{}/curve-track/{}/transition/{}".format(
        TEMPLATE_SET_ID,
        TRACK_NUMBER,
        end_name.lower(),
    )


def state_for_end(end_name, transition_length_mm):
    """Return one analysed state in the representative Entry/Exit pair."""
    if end_name not in ("Entry", "Exit"):
        raise ValueError("end_name must be 'Entry' or 'Exit'")
    if (
        isinstance(transition_length_mm, bool)
        or not isinstance(transition_length_mm, (int, float))
        or not math.isfinite(float(transition_length_mm))
        or float(transition_length_mm) <= 0.0
    ):
        raise ValueError(
            "transition_length_mm must be a finite positive number"
        )

    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    transition_length_mm = float(transition_length_mm)
    intent = api.TransitionIntent(
        transition_id=_transition_id(end_name),
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Track 2",
        end_name=end_name,
    )
    return api.analyse_transition_state(api.TransitionState(intent))


def initial_states():
    """Return the deterministic Entry/Exit pair in canonical order."""
    return (
        state_for_end("Entry", ENTRY_TRANSITION_LENGTH_MM),
        state_for_end("Exit", EXIT_TRANSITION_LENGTH_MM),
    )


def edited_exit_intent():
    """Return the one accepted-command replacement intent for the Exit."""
    return state_for_end(
        "Exit",
        EDITED_EXIT_TRANSITION_LENGTH_MM,
    ).intent


def failed_exit_intent():
    """Return the deterministic injected-failure replacement intent."""
    return state_for_end(
        "Exit",
        FAILED_EXIT_TRANSITION_LENGTH_MM,
    ).intent
