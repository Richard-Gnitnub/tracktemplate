"""Prepare an explicit reference rail-interface consistency proof.

The complete signed package, manifest and fixed model request pass the
existing research boundary first. The separate proof rejects inconsistent
reference rail inputs without changing prior assembly or model operations.
It supplies no package, rail-fit, production or redistribution acceptance.
"""

from dataclasses import dataclass

from tracktemplate.application.chair_model_research import (
    ChairModelResearchResult,
    prepare_chair_model_research,
)
from tracktemplate.application.chair_research import ChairResearchError
from tracktemplate.domain.chair_rail_interface import (
    ChairRailInterfaceProof,
    prove_chair_rail_interface,
)


class ChairRailResearchError(ChairResearchError):
    """Recoverable rail-reference refusal without document or file changes."""


@dataclass(frozen=True)
class ChairRailResearchResult:
    """Original validated inputs and geometry alongside exact equalities.

    The model result retains the original package, manifest, request and
    their signatures, plus both geometry scales and component identities.
    Adapters must prepare again from those complete inputs. A fabricated
    result is not authority to construct or accept geometry.
    """

    model_research: ChairModelResearchResult
    proof: ChairRailInterfaceProof


def prepare_chair_rail_research(package, manifest_text, request):
    """Validate the complete model request, then prove reference relations.

    Earlier package, manifest and request errors propagate unchanged.
    Only this new operation rejects rail quantities that disagree with
    their exact source equations. All work is in memory; no document,
    file, definition, signature or admission state is changed.
    """
    model = prepare_chair_model_research(package, manifest_text, request)
    try:
        proof = prove_chair_rail_interface(
            model.full_size_research.geometry, model.scale_denominator,
        )
    except (TypeError, ValueError, KeyError) as error:
        raise ChairRailResearchError(
            "research-rail-interface-inconsistent", "$.definition", str(error),
        ) from error
    return ChairRailResearchResult(model_research=model, proof=proof)
