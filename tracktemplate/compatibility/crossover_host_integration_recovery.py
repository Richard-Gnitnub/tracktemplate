"""Keep inherited crossover host integration inside one Undo transaction."""

from dataclasses import dataclass


class CrossoverHostIntegrationRecoveryError(RuntimeError):
    """The host integration command could not establish safe recovery."""


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
            raise CrossoverHostIntegrationRecoveryError(
                "The inherited host integration transaction changed."
            )
        self.opened = True

    def commitTransaction(self):
        if not self.opened or self.committed or self.aborted:
            raise CrossoverHostIntegrationRecoveryError(
                "The inherited host integration commit changed."
            )
        self.committed = True

    def abortTransaction(self):
        if not self.opened or self.committed or self.aborted:
            raise CrossoverHostIntegrationRecoveryError(
                "The inherited host integration abort changed."
            )
        self.aborted = True


@dataclass(frozen=True)
class CrossoverHostIntegrationRecoveryAdapter:
    """Run inherited create and remove with one real document transaction."""

    module: object
    original_create: object
    original_remove: object

    def _run(self, document, crossover_id, original, label):
        if int(document.UndoMode) != 1:
            raise CrossoverHostIntegrationRecoveryError(
                "Enable document Undo before changing crossover host "
                "integration."
            )
        if getattr(original, "__globals__", None) is not self.module.__dict__:
            raise CrossoverHostIntegrationRecoveryError(
                "The inherited host integration command changed."
            )
        proxy = _TransactionDocument(document, label)
        transaction_open = False
        try:
            document.openTransaction(label)
            transaction_open = True
            result = original(proxy, crossover_id)
            if not proxy.opened or not proxy.committed or proxy.aborted:
                raise CrossoverHostIntegrationRecoveryError(
                    "The inherited host integration did not commit once."
                )
            document.commitTransaction()
            transaction_open = False
            return result
        except Exception:
            if transaction_open:
                try:
                    document.abortTransaction()
                except Exception as error:
                    raise CrossoverHostIntegrationRecoveryError(
                        "The crossover host integration could not roll back."
                    ) from error
            raise

    def create(self, document, crossover_id):
        """Integrate the crossover and chair-display change as one command."""
        identifier = str(crossover_id or "").strip()
        label = (
            "Integrate Version {} crossover {} with host templates"
            .format(self.module.MACRO_VERSION_NUMBER, identifier)
        )
        return self._run(
            document, crossover_id, self.original_create, label,
        )

    def remove(self, document, crossover_id):
        """Restore original production records as one recoverable command."""
        identifier = str(crossover_id or "").strip()
        label = (
            "Remove Version {} crossover host integration {}"
            .format(self.module.MACRO_VERSION_NUMBER, identifier)
        )
        return self._run(
            document, crossover_id, self.original_remove, label,
        )
