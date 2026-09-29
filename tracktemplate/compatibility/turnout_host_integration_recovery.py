"""Keep inherited turnout host integration inside one Undo transaction.

This turnout compatibility module owns temporary duplication with the
crossover adapter until the B15 host meets its legacy-retirement gate.
"""

from dataclasses import dataclass


class TurnoutHostIntegrationRecoveryError(RuntimeError):
    """The turnout host command could not establish safe recovery."""


class _TransactionDocument:
    """Delegate document work while retaining the inherited commit boundary."""

    def __init__(self, document, expected_label):
        self._document = document
        self._expected_label = expected_label
        self.opened = False
        self.committed = False
        self.aborted = False

    def __getattr__(self, name):
        return getattr(self._document, name)

    def openTransaction(self, label):
        if self.opened or str(label) != self._expected_label:
            raise TurnoutHostIntegrationRecoveryError(
                "The inherited turnout host transaction changed."
            )
        self.opened = True

    def commitTransaction(self):
        if not self.opened or self.committed or self.aborted:
            raise TurnoutHostIntegrationRecoveryError(
                "The inherited turnout host commit changed."
            )
        self.committed = True

    def abortTransaction(self):
        if not self.opened or self.committed or self.aborted:
            raise TurnoutHostIntegrationRecoveryError(
                "The inherited turnout host abort changed."
            )
        self.aborted = True


@dataclass(frozen=True)
class TurnoutHostIntegrationRecoveryAdapter:
    """Run inherited Create and Remove with one real document transaction."""

    module: object
    original_create: object
    original_remove: object

    def _run(self, document, turnout_id, original, label):
        if int(document.UndoMode) != 1:
            raise TurnoutHostIntegrationRecoveryError(
                "Enable document Undo before changing turnout host "
                "integration."
            )
        if getattr(original, "__globals__", None) is not self.module.__dict__:
            raise TurnoutHostIntegrationRecoveryError(
                "The inherited turnout host command changed."
            )
        proxy = _TransactionDocument(document, label)
        transaction_open = False
        try:
            document.openTransaction(label)
            transaction_open = True
            result = original(proxy, turnout_id)
            if not proxy.opened or not proxy.committed or proxy.aborted:
                raise TurnoutHostIntegrationRecoveryError(
                    "The inherited turnout host command did not commit once."
                )
            document.commitTransaction()
            transaction_open = False
            return result
        except Exception:
            if transaction_open:
                try:
                    document.abortTransaction()
                except Exception as error:
                    raise TurnoutHostIntegrationRecoveryError(
                        "The turnout host integration could not roll back."
                    ) from error
            raise

    def create(self, document, turnout_id):
        """Integrate turnout and chair-display change as one command."""
        identifier = str(turnout_id or "").strip()
        label = (
            "Integrate Version {} turnout {} into host template"
            .format(self.module.MACRO_VERSION_NUMBER, identifier)
        )
        return self._run(document, turnout_id, self.original_create, label)

    def remove(self, document, turnout_id):
        """Restore production records as one recoverable command."""
        identifier = str(turnout_id or "").strip()
        label = (
            "Remove Version {} turnout host integration {}"
            .format(self.module.MACRO_VERSION_NUMBER, identifier)
        )
        return self._run(document, turnout_id, self.original_remove, label)
