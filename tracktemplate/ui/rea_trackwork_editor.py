"""Transient REA B/C controls over injected canonical trackwork commands."""

from dataclasses import dataclass
from dataclasses import replace

from tracktemplate.application.rea_turnout_state import (
    REA_INTENT_JSON_PROPERTY,
    ReaTrackworkIntent,
)
from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification


@dataclass(frozen=True)
class ReaHostChoice:
    """Display one existing host; its object reference guards stale input."""

    object_ref: object
    object_name: str
    template_set_id: str
    label: str


class ReaTrackworkEditorController:
    """Keep transient form state; delegate every write and rebuild."""

    def __init__(self, document, workflow, *, read_records, read_hosts,
                 active_document, new_entity_id):
        if not all(callable(port) for port in (
            read_records, read_hosts, active_document, new_entity_id,
        )) or not all(callable(getattr(workflow, name, None))
                      for name in ("create", "update", "rebuild")):
            raise TypeError("Complete REA editor command/read ports required.")
        self.document = document
        self.workflow = workflow
        self._read_records = read_records
        self._read_hosts = read_hosts
        self._active_document = active_document
        self._new_entity_id = new_entity_id
        self.records = ()
        self.hosts = ()
        self.cancel_edit()

    def _active(self):
        if self._active_document() is not self.document:
            raise ValueError(
                "The active document changed; reopen the REA B/C manager."
            )

    def _host_choices(self):
        choices = tuple(self._read_hosts(self.document))
        if (any(not isinstance(item, ReaHostChoice) for item in choices)
                or len({item.object_name for item in choices}) != len(choices)):
            raise ValueError("The current host choices are invalid.")
        return choices

    def refresh(self):
        """Read current records and hosts without calculating geometry."""
        self._active()
        records = tuple(self._read_records(self.document))
        hosts = self._host_choices()
        self.records, self.hosts = records, hosts
        self.cancel_edit()
        return records, hosts

    def _record(self, entity_id):
        self._active()
        expected = next((obj for obj, intent in self.records
                         if intent.entity_id == entity_id), None)
        current = next(((obj, intent)
                        for obj, intent in self._read_records(self.document)
                        if intent.entity_id == entity_id), None)
        if expected is None or current is None or current[0] is not expected:
            raise ValueError("The selected record changed; refresh and reload.")
        return current

    def _selected_hosts(self, names):
        if type(names) is not tuple or not names:
            raise ValueError("Select the existing host or ordered hosts.")
        current = {item.object_name: item for item in self._host_choices()}
        previous = {item.object_name: item for item in self.hosts}
        selected = []
        for name in names:
            old, live = previous.get(name), current.get(name)
            if (old is None or live is None
                    or old.object_ref is not live.object_ref
                    or old.template_set_id != live.template_set_id):
                raise ValueError("Host selection changed; refresh and reload.")
            selected.append(live)
        if len({item.template_set_id for item in selected}) != 1:
            raise ValueError("Select hosts from the same template set.")
        return tuple(selected)

    def begin_edit(self, entity_id):
        """Load the current canonical object without changing its state."""
        obj, intent = self._record(entity_id)
        self._selected_hosts(intent.host_names)
        self._editing_object = obj
        self.editing_intent = intent
        self._loaded_payload = getattr(obj, REA_INTENT_JSON_PROPERTY)
        return intent

    def cancel_edit(self):
        """Discard only the transient loaded selection."""
        self._editing_object = None
        self.editing_intent = None
        self._loaded_payload = None

    def create(self, *, entity_kind, host_names, switch_size, crossing_ratio,
               reference_chainage_mm, handing, orientation=None,
               arrangement=None, minimum_radius_mm=None):
        """Create from explicit source choices through the existing command."""
        self._active()
        hosts = self._selected_hosts(host_names)
        intent = ReaTrackworkIntent(
            entity_id=self._new_entity_id(), entity_kind=entity_kind,
            template_set_id=hosts[0].template_set_id, host_names=host_names,
            source_specification=ReaTurnoutSpecification(
                switch_size, crossing_ratio,
            ),
            reference_chainage_mm=reference_chainage_mm, handing=handing,
            orientation=orientation, arrangement=arrangement,
            minimum_radius_mm=minimum_radius_mm,
        )
        obj = self.workflow.create(self.document, intent)
        self.refresh()
        return obj

    def apply_changes(self, *, host_names, switch_size, crossing_ratio,
                      reference_chainage_mm, handing, orientation=None,
                      arrangement=None, minimum_radius_mm=None):
        """Refuse stale forms before preparing a replacement intent."""
        previous = self.editing_intent
        if previous is None:
            raise ValueError("Select a stored REA B/C record to edit.")
        obj, current = self._record(previous.entity_id)
        if (obj is not self._editing_object or current != previous
                or getattr(obj, REA_INTENT_JSON_PROPERTY)
                != self._loaded_payload):
            raise ValueError("The edited record changed; refresh and reload.")
        hosts = self._selected_hosts(host_names)
        if hosts[0].template_set_id != previous.template_set_id:
            raise ValueError("An edit must keep the original template set.")
        replacement = replace(
            previous, host_names=host_names,
            source_specification=replace(
                previous.source_specification, switch_size=switch_size,
                crossing_ratio=crossing_ratio,
            ),
            reference_chainage_mm=reference_chainage_mm, handing=handing,
            orientation=orientation, arrangement=arrangement,
            minimum_radius_mm=minimum_radius_mm,
        )
        result = self.workflow.update(self.document, obj, replacement)
        self.refresh()
        self.begin_edit(previous.entity_id)
        return result

    def rebuild(self, entity_id):
        """Rebuild only a current selected record; keep its canonical bytes."""
        obj, intent = self._record(entity_id)
        self._selected_hosts(intent.host_names)
        return self.workflow.rebuild(self.document, obj)


class ReaTrackworkEditorPanel:
    """Injected QWidget controls; form changes do not generate geometry."""

    def __init__(self, controller, qt_widgets, parent=None, *,
                 minimum_radius_mm):
        self.controller = controller
        self.last_result = None
        self.last_error = None
        self._available = False
        self._loaded_numbers = {}
        self.widget = qt_widgets.QWidget(parent)
        self.scroll_area = qt_widgets.QScrollArea(parent)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.widget)
        layout = qt_widgets.QVBoxLayout(self.widget)

        research = qt_widgets.QLabel(
            "Research. Source limits apply; production is unavailable. "
            "Use Rebuild display after reopening or changing a host."
        )
        research.setWordWrap(True)
        layout.addWidget(research)
        self.records_combo = qt_widgets.QComboBox()
        self.records_combo.setObjectName("TrackTemplateReaRecords")
        layout.addWidget(self.records_combo)
        self.identity_label = qt_widgets.QLabel("New REA B/C research record")
        layout.addWidget(self.identity_label)

        self.kind_combo = qt_widgets.QComboBox()
        self.kind_combo.addItem("Turnout", "turnout")
        self.kind_combo.addItem("Crossover", "crossover")
        self.size_combo = qt_widgets.QComboBox()
        self.size_combo.addItem("Select switch size", None)
        self.size_combo.addItem("B", "B")
        self.size_combo.addItem("C", "C")
        self.host_a_combo = qt_widgets.QComboBox()
        self.host_b_combo = qt_widgets.QComboBox()
        self.ratio_edit = qt_widgets.QLineEdit()
        self.chainage_edit = qt_widgets.QLineEdit()
        self.handing_combo = qt_widgets.QComboBox()
        self.direction_combo = qt_widgets.QComboBox()
        self.minimum_radius_edit = qt_widgets.QLineEdit()
        self.minimum_radius_edit.setText(repr(float(minimum_radius_mm)))

        self._field(layout, qt_widgets, "Trackwork", self.kind_combo)
        self._field(layout, qt_widgets, "Switch size", self.size_combo)
        self._field(layout, qt_widgets, "Crossing ratio 1:n (RAM)",
                    self.ratio_edit)
        self._field(layout, qt_widgets, "Host / reference host",
                    self.host_a_combo)
        self.host_b_label = self._field(
            layout, qt_widgets, "Second host", self.host_b_combo,
        )
        self._field(layout, qt_widgets, "Reference chainage (mm)",
                    self.chainage_edit)
        self._field(layout, qt_widgets, "Handing", self.handing_combo)
        self.direction_label = self._field(
            layout, qt_widgets, "Orientation", self.direction_combo,
        )
        self.minimum_radius_label = self._field(
            layout, qt_widgets, "Minimum radius (mm)",
            self.minimum_radius_edit,
        )
        self.status_label = qt_widgets.QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("TrackTemplateReaStatus")
        layout.addWidget(self.status_label)
        buttons = qt_widgets.QHBoxLayout()
        layout.addLayout(buttons)
        for name, label, callback in (
            ("create", "Create", self._on_create),
            ("edit", "Edit selected", self._on_edit),
            ("apply", "Apply", self._on_apply),
            ("cancel", "Cancel edit", self._on_cancel),
            ("rebuild", "Rebuild display", self._on_rebuild),
            ("refresh", "Refresh", self.refresh),
        ):
            button = qt_widgets.QPushButton(label)
            button.setObjectName("TrackTemplateRea" + name.title())
            button.clicked.connect(callback)
            setattr(self, name + "_button", button)
            buttons.addWidget(button)
        for name, widget in (
            ("Kind", self.kind_combo), ("Size", self.size_combo),
            ("Ratio", self.ratio_edit), ("Chainage", self.chainage_edit),
            ("HostA", self.host_a_combo), ("HostB", self.host_b_combo),
            ("Handing", self.handing_combo),
            ("Direction", self.direction_combo),
            ("MinimumRadius", self.minimum_radius_edit),
        ):
            widget.setObjectName("TrackTemplateRea" + name)
        self.kind_combo.currentIndexChanged.connect(self._mode_changed)
        self._mode_changed()
        self.refresh()

    @staticmethod
    def _field(layout, qt_widgets, title, widget):
        label = qt_widgets.QLabel(title)
        layout.addWidget(label)
        layout.addWidget(widget)
        return label

    def _mode_changed(self, _index=None):
        crossover = self.kind_combo.currentData() == "crossover"
        old_hand = self.handing_combo.currentText()
        self.handing_combo.clear()
        if crossover:
            self.handing_combo.addItem("Automatic handing")
        self.handing_combo.addItems(("Left-hand", "Right-hand"))
        match = self.handing_combo.findText(old_hand)
        if match >= 0:
            self.handing_combo.setCurrentIndex(match)
        self.direction_combo.clear()
        self.direction_combo.addItems(
            ("Facing crossover", "Trailing crossover") if crossover else (
                "Facing in host travel direction",
                "Trailing against host travel direction",
            )
        )
        self.direction_label.setText(
            "Arrangement" if crossover else "Orientation",
        )
        for widget in (self.host_b_combo, self.host_b_label,
                       self.minimum_radius_edit, self.minimum_radius_label):
            widget.setVisible(crossover)

    def _set_editing(self, editing):
        self.kind_combo.setEnabled(not editing)
        self.records_combo.setEnabled(not editing)
        self.create_button.setEnabled(self._available and not editing)
        self.apply_button.setEnabled(self._available and editing)
        self.cancel_button.setEnabled(editing)

    def _report_error(self, error):
        self.last_result = None
        self.last_error = error
        self.status_label.setText("Could not complete: {}".format(error))

    def _refresh_choices(self, selected_id=None):
        self.records_combo.clear()
        for obj, intent in self.controller.records:
            spec = intent.source_specification
            self.records_combo.addItem(
                "{} | {} | {} 1:{} {}".format(
                    intent.entity_id, obj.Label, spec.switch_size,
                    spec.crossing_ratio, intent.entity_kind,
                ), intent.entity_id,
            )
        if selected_id is not None:
            self.records_combo.setCurrentIndex(
                self.records_combo.findData(selected_id),
            )
        for combo in (self.host_a_combo, self.host_b_combo):
            old = combo.currentData()
            combo.clear()
            combo.addItem("Select host", None)
            for host in self.controller.hosts:
                combo.addItem(host.label, host.object_name)
            found = combo.findData(old)
            combo.setCurrentIndex(found if found >= 0 else 0)
        available = bool(self.controller.records)
        self.edit_button.setEnabled(available)
        self.rebuild_button.setEnabled(available)

    def refresh(self, _checked=False):
        """Refresh the source list without rebuilding any display."""
        try:
            self.controller.refresh()
            self._refresh_choices()
            self._available = True
            self._set_editing(False)
            self.identity_label.setText("New REA B/C research record")
            self._loaded_numbers = {}
            self.last_error = None
            self.status_label.setText("Research: ready for an explicit action.")
        except (TypeError, ValueError, RuntimeError) as error:
            self._available = False
            self._report_error(error)
            for button in (self.create_button, self.apply_button,
                           self.edit_button, self.rebuild_button):
                button.setEnabled(False)

    def _number(self, name, widget):
        text = widget.text().strip()
        previous = self._loaded_numbers.get(name)
        if previous is not None and text == previous[0]:
            return previous[1]
        try:
            return float(text)
        except (ValueError, OverflowError) as error:
            raise ValueError("Enter a numeric {}.".format(name)) from error

    def _values(self):
        crossover = self.kind_combo.currentData() == "crossover"
        hosts = (self.host_a_combo.currentData(),)
        if crossover:
            hosts += (self.host_b_combo.currentData(),)
        return dict(
            host_names=hosts, switch_size=self.size_combo.currentData(),
            crossing_ratio=self._number("crossing ratio", self.ratio_edit),
            reference_chainage_mm=self._number(
                "chainage (mm)", self.chainage_edit,
            ),
            handing=self.handing_combo.currentText(),
            orientation=(None if crossover else
                         self.direction_combo.currentText()),
            arrangement=(self.direction_combo.currentText()
                         if crossover else None),
            minimum_radius_mm=(self._number(
                "minimum radius (mm)", self.minimum_radius_edit,
            ) if crossover else None),
        )

    def _load_form(self, intent):
        self.kind_combo.setCurrentIndex(
            self.kind_combo.findData(intent.entity_kind),
        )
        self.size_combo.setCurrentIndex(self.size_combo.findData(
            intent.source_specification.switch_size,
        ))
        self.host_a_combo.setCurrentIndex(self.host_a_combo.findData(
            intent.host_names[0],
        ))
        if intent.entity_kind == "crossover":
            self.host_b_combo.setCurrentIndex(self.host_b_combo.findData(
                intent.host_names[1],
            ))
        self.handing_combo.setCurrentIndex(self.handing_combo.findText(
            intent.handing,
        ))
        self.direction_combo.setCurrentIndex(self.direction_combo.findText(
            intent.orientation or intent.arrangement,
        ))
        self._loaded_numbers = {}
        for name, widget, number in (
            ("crossing ratio", self.ratio_edit,
             intent.source_specification.crossing_ratio),
            ("chainage (mm)", self.chainage_edit, intent.reference_chainage_mm),
            ("minimum radius (mm)", self.minimum_radius_edit,
             intent.minimum_radius_mm),
        ):
            if number is not None:
                text = repr(number)
                widget.setText(text)
                self._loaded_numbers[name] = (text, number)
        self.identity_label.setText(
            "{} | {} | research".format(intent.entity_id,
                                         intent.template_set_id),
        )
        self._set_editing(True)

    def _on_create(self, _checked=False):
        try:
            obj = self.controller.create(
                entity_kind=self.kind_combo.currentData(), **self._values(),
            )
            identifier = next(intent.entity_id
                              for candidate, intent in self.controller.records
                              if candidate is obj)
            self._refresh_choices(identifier)
            self.last_result, self.last_error = obj, None
            self.status_label.setText("Created REA B/C research trackwork.")
        except (TypeError, ValueError, RuntimeError) as error:
            self._report_error(error)

    def _on_edit(self, _checked=False):
        try:
            intent = self.controller.begin_edit(
                self.records_combo.currentData(),
            )
            self._load_form(intent)
            self.last_error = None
            self.status_label.setText("Editing REA B/C research trackwork.")
        except (TypeError, ValueError, RuntimeError) as error:
            self._report_error(error)

    def _on_apply(self, _checked=False):
        try:
            obj = self.controller.apply_changes(**self._values())
            intent = self.controller.editing_intent
            self._refresh_choices(intent.entity_id)
            self._load_form(intent)
            self.last_result, self.last_error = obj, None
            self.status_label.setText("REA B/C research changes applied.")
        except (TypeError, ValueError, RuntimeError) as error:
            self._report_error(error)

    def _on_cancel(self, _checked=False):
        self.controller.cancel_edit()
        self._set_editing(False)
        self.size_combo.setCurrentIndex(0)
        self.ratio_edit.setText("")
        self.chainage_edit.setText("")
        self._loaded_numbers = {}
        self.identity_label.setText("New REA B/C research record")
        self.last_result = None
        if self._available:
            self.last_error = None
            self.status_label.setText("Edit cancelled; no changes applied.")

    def _on_rebuild(self, _checked=False):
        try:
            self.last_result = self.controller.rebuild(
                self.records_combo.currentData(),
            )
            self.last_error = None
            self.status_label.setText("REA B/C research display rebuilt.")
        except (TypeError, ValueError, RuntimeError) as error:
            self._report_error(error)


def attach_rea_trackwork_panel(dialog, controller, qt_widgets, *,
                              minimum_radius_mm):
    """Append one source QWidget tab without replacing inherited callbacks."""
    if dialog.doc is not controller.document:
        raise ValueError("The REA panel and manager must use one document.")
    existing = getattr(dialog, "_tracktemplate_rea_panel", None)
    if existing is not None:
        if existing.controller is not controller:
            raise ValueError("The manager already has a different REA editor.")
        return existing
    panel = ReaTrackworkEditorPanel(
        controller, qt_widgets, dialog, minimum_radius_mm=minimum_radius_mm,
    )
    dialog.mode_tabs.addTab(panel.scroll_area, "REA B/C")
    dialog._tracktemplate_rea_panel = panel
    return panel
