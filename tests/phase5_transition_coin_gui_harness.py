"""Share exact primitives across the Phase 5 Coin GUI test harnesses."""

from tracktemplate.presentation import (
    transition_coin_viewprovider as viewprovider,
)


def _process_gui(update_gui, process_events):
    """Process five FreeCAD and Qt event cycles."""
    for _iteration in range(5):
        update_gui()
        process_events()


class _SelectionObserver:
    """Record FreeCAD selection callbacks for GUI assertions."""

    def __init__(self):
        self.events = []

    def addSelection(
        self,
        document_name,
        object_name,
        subelement_name,
        point,
    ):
        self.events.append(
            (
                str(document_name),
                str(object_name),
                str(subelement_name),
                tuple(float(value) for value in point),
            )
        )


class _ObservedTransitionCoinViewProviderFixture(
    viewprovider.TransitionCoinViewProviderFixture
):
    """Count Coin pick callbacks while retaining fixture behaviour."""

    def __init__(self, *args, **kwargs):
        self.pick_callback_count = 0
        super().__init__(*args, **kwargs)

    def getElementPicked(self, picked_point):
        self.pick_callback_count += 1
        return super().getElementPicked(picked_point)
