"""Recover the inherited crossover B4 command's first-tag failure."""

from dataclasses import dataclass
import inspect


class CrossoverB4RecoveryError(RuntimeError):
    """The B4 command could not prove cleanup of its new object."""


@dataclass(frozen=True)
class CrossoverB4RecoveryAdapter:
    """Guard one inherited B4 apply without changing its successful result."""

    module: object
    original_apply: object

    def _new_object_is_owned(self, doc, obj, name, identifier):
        """Accept only the untagged object created for this B4 command."""
        prefix = "CrossoverB4Timbering_{}".format(
            identifier.replace("-", "_"),
        )
        return (
            name.startswith(prefix)
            and str(getattr(obj, "TypeId", "")) == "Part::Feature"
            and str(getattr(obj, "Label", "")) == (
                "{} Automatically Resolved Timbering".format(identifier)
            )
            and not self.module.object_string_property(
                obj, "GeneratedRole", "",
            )
            and not self.module.object_string_property(
                obj, "CrossoverID", "",
            )
            and doc.getObject(name) is not None
        )

    def apply(self, *args, **kwargs):
        """Remove a known orphan after B15 aborts a failed first B4 tag."""
        request = inspect.signature(self.original_apply).bind(*args, **kwargs)
        doc = request.arguments["doc"]
        identifier = str(request.arguments["crossover_id"] or "").strip()
        before_names = {str(obj.Name) for obj in doc.Objects}
        before_history = (int(doc.UndoCount), int(doc.RedoCount))
        before_config = self.module.crossover_config_by_id(
            doc, identifier,
        )
        original_tagger = self.module.tag_generated_object
        failed_new_b4_tag = None

        def guarded_tagger(obj, role, template_set_id):
            nonlocal failed_new_b4_tag
            try:
                return original_tagger(obj, role, template_set_id)
            except Exception:
                name = str(getattr(obj, "Name", ""))
                if (
                    str(role) == str(self.module.CROSSOVER_B4_ROLE)
                    and name not in before_names
                ):
                    failed_new_b4_tag = name
                raise

        self.module.tag_generated_object = guarded_tagger
        try:
            try:
                return self.original_apply(*args, **kwargs)
            except Exception as error:
                if failed_new_b4_tag is None:
                    raise
                orphan = doc.getObject(failed_new_b4_tag)
                if orphan is not None:
                    if not self._new_object_is_owned(
                        doc, orphan, failed_new_b4_tag, identifier,
                    ):
                        raise CrossoverB4RecoveryError(
                            "The failed crossover timbering object cannot be "
                            "identified for cleanup."
                        ) from error
                    try:
                        doc.removeObject(failed_new_b4_tag)
                    except Exception as cleanup_error:
                        raise CrossoverB4RecoveryError(
                            "The failed crossover timbering object could not "
                            "be removed."
                        ) from cleanup_error
                after_names = {str(obj.Name) for obj in doc.Objects}
                after_history = (int(doc.UndoCount), int(doc.RedoCount))
                after_config = self.module.crossover_config_by_id(
                    doc, identifier,
                )
                if (
                    after_names != before_names
                    or after_history != before_history
                    or after_config != before_config
                ):
                    raise CrossoverB4RecoveryError(
                        "The failed crossover timbering command did not "
                        "restore its document state."
                    ) from error
                raise
        finally:
            self.module.tag_generated_object = original_tagger
