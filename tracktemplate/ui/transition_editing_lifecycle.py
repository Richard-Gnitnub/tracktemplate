"""Explicit transient lifecycle for one transition-view editing session."""

from tracktemplate.ui.transition_parameter_editor import (
    TransitionParameterEditorController,
)


__all__ = (
    "TRANSITION_EDITING_LIFECYCLE_ID",
    "TransitionEditingLifecycle",
    "TransitionEditingLifecycleError",
)


TRANSITION_EDITING_LIFECYCLE_ID = (
    "tracktemplate.transition-editing-lifecycle.development.v1"
)


class TransitionEditingLifecycleError(RuntimeError):
    """Report an activation or cleanup failure without widening authority."""

    def __init__(self, code, message):
        self.code = str(code)
        self.detail = str(message)
        super().__init__("{}: {}".format(self.code, self.detail))


def _lifecycle_error(code, message):
    return TransitionEditingLifecycleError(code, message)


def _require_callback(value, name):
    if not callable(value):
        raise TypeError("{} must be callable".format(name))
    return value


def _attachment_transition_ids(attachment):
    try:
        attached = attachment.attached
        count = int(attachment.attachment_count)
        transition_ids = tuple(attachment.transition_ids)
        dispose = attachment.dispose
    except Exception as error:
        raise TypeError(
            "attachment_factory must return a document attachment"
        ) from error
    if attached is not True or not callable(dispose):
        raise TypeError("the document attachment must be active and disposable")
    if (
        count < 1
        or count != len(transition_ids)
        or len(set(transition_ids)) != len(transition_ids)
        or any(
            not isinstance(identity, str) or not identity
            for identity in transition_ids
        )
    ):
        raise ValueError(
            "the document attachment must contain unique transition identities"
        )
    return transition_ids


class TransitionEditingLifecycle:
    """Own one explicit, once-only attachment and transient editor dialog."""

    def __init__(
        self,
        *,
        attachment_factory,
        selection_reader,
        selection_clearer,
        dialog_factory,
        cleanup_callback,
    ):
        self._attachment_factory = _require_callback(
            attachment_factory,
            "attachment_factory",
        )
        self._selection_reader = _require_callback(
            selection_reader,
            "selection_reader",
        )
        self._selection_clearer = _require_callback(
            selection_clearer,
            "selection_clearer",
        )
        self._dialog_factory = _require_callback(
            dialog_factory,
            "dialog_factory",
        )
        self._cleanup_callback = _require_callback(
            cleanup_callback,
            "cleanup_callback",
        )
        self._controller = TransitionParameterEditorController(
            self._selection_reader
        )
        self._attachment = None
        self._dialog = None
        self._transition_ids = ()
        self._selection_cleared = True
        self._state = "inactive"

    @property
    def state(self):
        """Return the explicit lifecycle state."""
        return self._state

    @property
    def active(self):
        """Return whether selection and editing are currently available."""
        return self._state == "active"

    @property
    def transition_ids(self):
        """Return attached stable identities while cleanup is owned here."""
        return self._transition_ids

    @property
    def attachment(self):
        """Return the live attachment for bounded composition inspection."""
        if self._attachment is None:
            raise _lifecycle_error(
                "transition-editing-not-active",
                "the transition attachment is not available",
            )
        return self._attachment

    def _retire(self):
        self._attachment_factory = None
        self._selection_reader = None
        self._selection_clearer = None
        self._dialog_factory = None
        self._cleanup_callback = None
        self._controller = None
        self._attachment = None
        self._dialog = None
        self._transition_ids = ()
        self._state = "retired"

    def activate(self):
        """Attach every supported transition once after explicit activation."""
        if self._state == "active":
            raise _lifecycle_error(
                "transition-editing-already-active",
                "this transition-editing lifecycle is already active",
            )
        if self._state != "inactive":
            raise _lifecycle_error(
                "transition-editing-retired",
                "a used transition-editing lifecycle cannot be reactivated",
            )

        self._state = "activating"
        try:
            attachment = self._attachment_factory()
        except Exception as error:
            self._retire()
            raise _lifecycle_error(
                "transition-editing-activation-failed",
                str(error),
            ) from error

        self._attachment = attachment
        try:
            transition_ids = _attachment_transition_ids(attachment)
        except Exception as error:
            cleanup_error = None
            try:
                attachment.dispose()
            except Exception as observed_cleanup_error:
                cleanup_error = observed_cleanup_error
            if cleanup_error is None:
                self._retire()
            else:
                self._state = "cleanup-failed"
            detail = str(error)
            if cleanup_error is not None:
                detail += "; cleanup also failed: {}".format(cleanup_error)
            raise _lifecycle_error(
                "transition-editing-activation-failed",
                detail,
            ) from error

        self._transition_ids = transition_ids
        self._selection_cleared = False
        self._state = "active"
        return transition_ids

    def show_editor(self):
        """Show the existing transient editor for the current selection."""
        if not self.active:
            raise _lifecycle_error(
                "transition-editing-not-active",
                "activate transition editing before showing the editor",
            )
        if self._dialog is None:
            try:
                dialog = self._dialog_factory(self._controller)
                if any(
                    not callable(getattr(dialog, name, None))
                    for name in ("show", "close")
                ):
                    raise TypeError(
                        "dialog_factory must return a showable, closable dialog"
                    )
                self._dialog = dialog
            except Exception as error:
                raise _lifecycle_error(
                    "transition-editing-editor-failed",
                    str(error),
                ) from error
        try:
            refresh_selection = getattr(
                self._dialog,
                "refresh_selection",
                None,
            )
            if callable(refresh_selection):
                refresh_selection()
            self._dialog.show()
        except Exception as error:
            raise _lifecycle_error(
                "transition-editing-editor-failed",
                str(error),
            ) from error
        return self._dialog

    def deactivate(self):
        """Close the editor and dispose all live derived attachment state."""
        if self._state in ("inactive", "retired"):
            return ()
        if self._state not in ("active", "cleanup-failed"):
            raise _lifecycle_error(
                "transition-editing-cleanup-failed",
                "transition editing cannot deactivate from {!r}".format(
                    self._state
                ),
            )

        self._state = "deactivating"
        cleanup_errors = []
        if self._dialog is not None:
            try:
                self._dialog.close()
            except Exception as error:
                cleanup_errors.append("editor close failed: {}".format(error))
            else:
                self._dialog = None
        if not self._selection_cleared:
            try:
                self._selection_clearer()
            except Exception as error:
                cleanup_errors.append(
                    "selection cleanup failed: {}".format(error)
                )
            else:
                self._selection_cleared = True
        if self._attachment is not None:
            try:
                self._attachment.dispose()
            except Exception as error:
                cleanup_errors.append(
                    "document attachment cleanup failed: {}".format(error)
                )
            else:
                self._attachment = None
        if not cleanup_errors and self._cleanup_callback is not None:
            try:
                self._cleanup_callback()
            except Exception as error:
                cleanup_errors.append(
                    "lifecycle cleanup failed: {}".format(error)
                )
            else:
                self._cleanup_callback = None

        if cleanup_errors:
            self._state = "cleanup-failed"
            raise _lifecycle_error(
                "transition-editing-cleanup-failed",
                "; ".join(cleanup_errors),
            )

        transition_ids = self._transition_ids
        self._retire()
        return transition_ids
