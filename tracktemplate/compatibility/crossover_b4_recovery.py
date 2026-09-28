"""Guard inherited crossover B4 recovery and result persistence."""

from dataclasses import dataclass
import inspect


class CrossoverB4RecoveryError(RuntimeError):
    """The B4 command could not prove cleanup of its new object."""


@dataclass(frozen=True)
class CrossoverB4RecoveryAdapter:
    """Guard one inherited B4 apply and persist its final analysis."""

    module: object
    original_apply: object
    original_writer: object

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
        """Persist final analysis or remove a known first-tag orphan."""
        request = inspect.signature(self.original_apply).bind(*args, **kwargs)
        doc = request.arguments["doc"]
        identifier = str(request.arguments["crossover_id"] or "").strip()
        writer_name = "_write_crossover_b4_and_timber_analysis_metadata"
        original_writer = getattr(self.module, writer_name, None)
        if original_writer is not self.original_writer:
            raise CrossoverB4RecoveryError(
                "The inherited crossover timbering metadata writer changed."
            )
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

        def guarded_writer(writer_doc, config, b4_result, analysis_result):
            if writer_doc is not doc:
                raise CrossoverB4RecoveryError(
                    "The crossover timbering metadata document changed."
                )
            b4_result["resolved_analysis"] = dict(analysis_result)
            return original_writer(
                writer_doc, config, b4_result, analysis_result,
            )

        try:
            self.module.tag_generated_object = guarded_tagger
            setattr(self.module, writer_name, guarded_writer)
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
            setattr(self.module, writer_name, original_writer)
            self.module.tag_generated_object = original_tagger
