from ..data_slice_widget import SliceWidget
from ..slice_widget import MultiSliceWidgetHelper

from echo import CallbackProperty, HasCallbackProperties
from glue.core import Data
from glue_qt.utils import process_events
from numpy import arange
from qtpy.QtWidgets import QVBoxLayout, QWidget


class ViewerTestState(HasCallbackProperties):
    x_att = CallbackProperty()
    y_att = CallbackProperty()
    reference_data = CallbackProperty()
    slices = CallbackProperty()


class TestMultiSliceWidgetHelper(object):

    def test_replaced_sliders_stay_hidden(self):
        x = arange(360).reshape((3, 4, 5, 6))
        data = Data(x=x, label="Hypercube")

        state = ViewerTestState()
        state.reference_data = data
        state.x_att = data.pixel_component_ids[3]
        state.y_att = data.pixel_component_ids[2]
        state.slices = (0,) * data.ndim

        widget = QWidget()
        helper = MultiSliceWidgetHelper(viewer_state=state, layout=QVBoxLayout(widget))
        widget.show()
        process_events()

        # Two rebuilds in a row: the sliders of the first are replaced before
        # Qt has shown them, and Qt should not show them afterwards
        state.x_att = data.pixel_component_ids[1]
        state.y_att = data.pixel_component_ids[0]
        process_events()

        visible = {s for s in widget.findChildren(SliceWidget) if s.isVisible()}
        assert visible == {s for s in helper._sliders if s is not None}
        widget.close()

    def test_no_slider_if_flat(self):
        x = arange(72).reshape((6, 4, 1, 3))
        data = Data(x=x, label="Flat Cube")

        state = ViewerTestState()
        state.reference_data = data
        state.x_att = data.pixel_component_ids[0]
        state.y_att = data.pixel_component_ids[1]
        state.slices = (0,) * data.ndim

        layout = QVBoxLayout()

        helper = MultiSliceWidgetHelper(viewer_state=state, layout=layout)
        assert helper._sliders[2] is None
        assert isinstance(helper._sliders[3], SliceWidget)
