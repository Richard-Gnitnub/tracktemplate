"""Guard inherited crossover B4 recovery and result persistence."""

from dataclasses import dataclass
import inspect
import time


class CrossoverB4RecoveryError(RuntimeError):
    """The B4 command could not prove cleanup of its new object."""


@dataclass(frozen=True)
class CrossoverB4RecoveryAdapter:
    """Guard one inherited B4 apply and persist its final analysis."""

    module: object
    original_apply: object
    original_writer: object
    original_signature: object = None
    original_current: object = None

    def resolution_signature(
        self, config, settings, inherited_signature, shared_result,
        b3_result, records, unresolved,
    ):
        """Keep B16 B4 resolution independent of display visibility."""
        settings = self.module.normalise_crossover_b4_settings(settings)
        settings["show_b4_geometry"] = True
        return self.original_signature(
            config, settings, inherited_signature, shared_result,
            b3_result, records, unresolved,
        )

    def result_is_current(self, config, inherited_records, result):
        """Also recognise an unchanged legacy hidden result without writing it."""
        if self.original_current(config, inherited_records, result):
            return True
        if not isinstance(result, dict) or not isinstance(config, dict):
            return False
        settings = self.module.normalise_crossover_b4_settings(
            result.get("settings")
        )
        if settings["show_b4_geometry"]:
            return False
        signature_inputs = (
            config, settings, result.get("inherited_signature"),
            result.get("shared_result"), result.get("b3_result"),
            result.get("resolved_timbers"), result.get("unresolved"),
        )
        legacy_signature = self.original_signature(*signature_inputs)
        if (
            str(result.get("resolution_signature") or "")
            != legacy_signature
            or str(config.get("b4_signature") or legacy_signature)
            != legacy_signature
        ):
            return False
        current_signature = self.resolution_signature(*signature_inputs)
        current_result = dict(result, resolution_signature=current_signature)
        current_config = dict(config, b4_signature=current_signature)
        return self.original_current(
            current_config, inherited_records, current_result,
        )

    def _display_only_reuse(self, request, doc, identifier, config):
        """Return a current B4 result when only visibility changed."""
        if (
            self.original_signature is None
            or self.original_current is None
            or not isinstance(config, dict)
            or bool(config.get("integration_active", False))
        ):
            return None
        stored = config.get("b4_result")
        if not isinstance(stored, dict) or not stored.get("applied"):
            return None
        module = self.module
        stored_settings = module.normalise_crossover_b4_settings(
            stored.get("settings")
        )
        obj = module._crossover_b4_object(doc, identifier)
        if obj is None:
            return None
        view = getattr(obj, "ViewObject", None)
        live_visibility = None
        if view is not None and hasattr(view, "Visibility"):
            live_visibility = bool(view.Visibility)
        requested_settings = module.normalise_crossover_b4_settings(
            request.get("b4_settings") or config.get("b4_settings")
        )
        if not request.get("b4_settings") and live_visibility is not None:
            requested_settings["show_b4_geometry"] = live_visibility
        if (
            module.normalise_crossover_b4_settings(config.get("b4_settings"))
            != stored_settings
            or requested_settings["show_b4_geometry"]
            == stored_settings["show_b4_geometry"]
        ):
            return None
        stored_calculation = dict(stored_settings)
        requested_calculation = dict(requested_settings)
        stored_calculation.pop("show_b4_geometry", None)
        requested_calculation.pop("show_b4_geometry", None)
        if stored_calculation != requested_calculation:
            return None
        settings_pairs = (
            (
                module.normalise_crossover_timber_analysis_settings,
                stored.get("analysis_settings"),
                config.get("timber_analysis_settings"),
            ),
            (
                module.normalise_crossover_shared_timber_settings,
                stored.get("shared_settings"),
                request.get("shared_settings")
                or config.get("shared_timber_settings"),
            ),
            (
                module.normalise_crossover_b3_settings,
                stored.get("b3_settings"),
                request.get("b3_settings") or config.get("b3_settings"),
            ),
        )
        if any(
            normalise(stored_value) != normalise(requested_value)
            for normalise, stored_value, requested_value in settings_pairs
        ):
            return None
        if not self.result_is_current(
            config, module.crossover_inherited_timber_records(doc, config),
            stored,
        ):
            return None
        if live_visibility is None:
            raise CrossoverB4RecoveryError(
                "The crossover timbering display is unavailable."
            )
        desired_visibility = requested_settings["show_b4_geometry"]
        try:
            if live_visibility != desired_visibility:
                view.Visibility = desired_visibility
            if bool(view.Visibility) != desired_visibility:
                raise CrossoverB4RecoveryError(
                    "The crossover timbering visibility did not change."
                )
        except Exception as error:
            if bool(view.Visibility) != live_visibility:
                try:
                    view.Visibility = live_visibility
                except Exception as cleanup_error:
                    raise CrossoverB4RecoveryError(
                        "The crossover timbering visibility could not be "
                        "restored."
                    ) from cleanup_error
            raise CrossoverB4RecoveryError(
                "The crossover timbering visibility could not be set."
            ) from error
        return dict(
            stored, cache_reused=True, settings=requested_settings,
        )

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
        started = time.perf_counter()
        request = inspect.signature(self.original_apply).bind(*args, **kwargs)
        request.apply_defaults()
        doc = request.arguments["doc"]
        identifier = str(request.arguments["crossover_id"] or "").strip()
        writer_name = "_write_crossover_b4_and_timber_analysis_metadata"
        original_writer = getattr(self.module, writer_name, None)
        if original_writer is not self.original_writer:
            raise CrossoverB4RecoveryError(
                "The inherited crossover timbering metadata writer changed."
            )
        before_config = self.module.crossover_config_by_id(
            doc, identifier,
        )
        reused = self._display_only_reuse(
            request.arguments, doc, identifier, before_config,
        )
        if reused is not None:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            reused["performance_timings_ms"] = dict(
                reused.get("performance_timings_ms") or {},
                incremental_reuse_lookup=elapsed_ms,
                pipeline_total=elapsed_ms,
            )
            return reused
        before_names = {str(obj.Name) for obj in doc.Objects}
        before_history = (int(doc.UndoCount), int(doc.RedoCount))
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
