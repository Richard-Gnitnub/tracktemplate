"""Internal application decision for inherited turnout edit reporting."""


__all__ = ()


def turnout_configuration_change_summary(
    old_config,
    new_config,
    rail_revision_fallback,
    timber_revision_fallback,
):
    """Return the inherited ordered changes before a turnout edit."""
    old = old_config if isinstance(old_config, dict) else {}
    new = new_config if isinstance(new_config, dict) else {}
    changes = []
    specifications = (
        ("toe_chainage", "Switch-toe chainage", "{:.3f} mm"),
        ("handing", "Handing", "{}"),
        ("orientation", "Orientation", "{}"),
        ("track_gauge", "Track gauge", "{:.3f} mm"),
        ("flangeway", "Design flangeway", "{:.3f} mm"),
        ("timber_outlines", "Timber outlines", "{}"),
        ("timber_centres", "Timber centre lines", "{}"),
        ("timber_numbers", "Timber identities", "{}"),
        ("timber_length_labels", "Timber length labels", "{}"),
        ("construction_marks", "Construction datums", "{}"),
    )
    for key, label, pattern in specifications:
        old_value = old.get(key)
        new_value = new.get(key)
        if key in ("toe_chainage", "track_gauge", "flangeway"):
            try:
                unchanged = abs(float(old_value) - float(new_value)) <= 1.0e-9
            except Exception:
                unchanged = old_value == new_value
        else:
            unchanged = old_value == new_value
        if unchanged:
            continue
        if key in (
            "timber_outlines", "timber_centres", "timber_numbers",
            "timber_length_labels", "construction_marks",
        ):
            old_text = "enabled" if bool(old_value) else "disabled"
            new_text = "enabled" if bool(new_value) else "disabled"
        elif key in ("toe_chainage", "track_gauge", "flangeway"):
            old_text = pattern.format(float(old_value))
            new_text = pattern.format(float(new_value))
        else:
            old_text = pattern.format(old_value)
            new_text = pattern.format(new_value)
        changes.append("{}: {} -> {}".format(label, old_text, new_text))
    old_revision = int(old.get("rail_geometry_revision") or 0)
    new_revision = int(
        new.get("rail_geometry_revision") or rail_revision_fallback()
    )
    if old_revision != new_revision:
        changes.append(
            "Rail construction geometry: revision {} -> revision {} (complete common crossing, vee, wing and check rails)".format(
                old_revision, new_revision
            )
        )
    old_timber_revision = int(old.get("timber_geometry_revision") or 0)
    new_timber_revision = int(
        new.get("timber_geometry_revision") or timber_revision_fallback()
    )
    if old_timber_revision != new_timber_revision:
        changes.append(
            "Turnout timbering: revision {} -> revision {} (REA switch, closure, crossing and exit timber outlines)".format(
                old_timber_revision, new_timber_revision
            )
        )
    return changes
