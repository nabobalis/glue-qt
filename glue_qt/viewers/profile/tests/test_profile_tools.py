from unittest.mock import patch

import numpy as np

from numpy.testing import assert_allclose

from glue.core import Data
from glue.core.fitters import PolynomialFitter
from glue_qt.core.fitters import FitSettingsWidget
from glue_qt.tests.helpers import requires_pyqt
from glue_qt.app import GlueApplication
from glue_qt.utils import process_events
from glue.viewers.image.state import AggregateSlice

from glue_qt.viewers.image import ImageViewer
from glue.viewers.profile.tests.test_state import SimpleCoordinates
from ..data_viewer import ProfileViewer


def set_degree(profile_tools, degree):
    # Set the polynomial degree in the settings dialog and click OK

    def exec_(dialog):
        dialog.widgets['degree'].setValue(degree)
        dialog.accept()

    with patch.object(FitSettingsWidget, 'exec_', exec_):
        profile_tools.ui.button_settings.click()


def fit_coefficients(viewer, profile_tools):
    # Fit from 0.9 to 15.1 in pixel coordinates and return the coefficients

    viewer.state.x_att = viewer.state.reference_data.pixel_component_ids[0]
    viewer.layers[0].wait()
    process_events()

    x, y = viewer.axes.transData.transform([[0.9, 4]])[0]
    viewer.axes.figure.canvas.button_press_event(x, y, 1)
    x, y = viewer.axes.transData.transform([[15.1, 4]])[0]
    viewer.axes.figure.canvas.motion_notify_event(x, y, 1)

    profile_tools.ui.button_fit.click()
    profile_tools.wait_for_fit()
    process_events()

    log = profile_tools.text_log.toPlainText().splitlines()
    assert log[:2] == ['d1', 'Coefficients:']
    return log[2:]


class TestProfileTools(object):

    def setup_method(self, method):

        self.data = Data(label='d1')
        self.data.coords = SimpleCoordinates()
        self.data['x'] = np.arange(240).reshape((30, 4, 2)).astype(float)

        self.app = GlueApplication()
        self.session = self.app.session
        self.hub = self.session.hub

        self.data_collection = self.session.data_collection
        self.data_collection.append(self.data)

        self.viewer = self.app.new_data_viewer(ProfileViewer)
        self.viewer.state.function = 'mean'

        self.viewer.toolbar.active_tool = 'profile-analysis'

        self.profile_tools = self.viewer.toolbar.tools['profile-analysis']._profile_tools

    def teardown_method(self, method):
        self.viewer.close()
        self.viewer = None
        self.app.close()
        self.app = None

    def test_navigate_sync_image(self):

        self.viewer.add_data(self.data)
        image_viewer = self.app.new_data_viewer(ImageViewer)
        image_viewer.add_data(self.data)
        assert image_viewer.state.slices == (0, 0, 0)

        self.viewer.state.x_att = self.data.pixel_component_ids[0]

        # Force events to be processed to make sure that the callback functions
        # for the computation thread are executed (since they rely on signals)
        self.viewer.layers[0].wait()
        process_events()

        x, y = self.viewer.axes.transData.transform([[1, 4]])[0]
        self.viewer.axes.figure.canvas.button_press_event(x, y, 1)
        self.viewer.axes.figure.canvas.button_release_event(x, y, 1)
        assert image_viewer.state.slices == (1, 0, 0)

        self.viewer.state.x_att = self.data.world_component_ids[0]

        x, y = self.viewer.axes.transData.transform([[10, 4]])[0]
        self.viewer.axes.figure.canvas.button_press_event(x, y, 1)
        self.viewer.axes.figure.canvas.button_release_event(x, y, 1)
        assert image_viewer.state.slices == (5, 0, 0)

    @requires_pyqt
    def test_fit_polynomial(self):

        # TODO: need to deterministically set to polynomial fitter

        self.viewer.add_data(self.data)
        self.profile_tools.ui.tabs.setCurrentIndex(1)

        # First try in pixel coordinates

        self.viewer.state.x_att = self.data.pixel_component_ids[0]

        # Force events to be processed to make sure that the callback functions
        # for the computation thread are executed (since they rely on signals)
        self.viewer.layers[0].wait()
        process_events()

        x, y = self.viewer.axes.transData.transform([[0.9, 4]])[0]
        self.viewer.axes.figure.canvas.button_press_event(x, y, 1)
        x, y = self.viewer.axes.transData.transform([[15.1, 4]])[0]
        self.viewer.axes.figure.canvas.motion_notify_event(x, y, 1)

        assert_allclose(self.profile_tools.rng_mode.state.x_range, (0.9, 15.1))

        self.profile_tools.ui.button_fit.click()
        self.profile_tools.wait_for_fit()

        # Force events to be processed to make sure that the callback functions
        # for the computation thread are executed (since they rely on signals)
        process_events()

        pixel_log = self.profile_tools.text_log.toPlainText().splitlines()
        assert pixel_log[0] == 'd1'
        assert pixel_log[1] == 'Coefficients:'
        assert pixel_log[-2] == '8.000000e+00'
        assert pixel_log[-1] == '3.500000e+00'

        self.profile_tools.ui.button_clear.click()
        assert self.profile_tools.text_log.toPlainText() == ''

        # Next, try in world coordinates

        self.viewer.state.x_att = self.data.world_component_ids[0]

        x, y = self.viewer.axes.transData.transform([[1.9, 4]])[0]
        self.viewer.axes.figure.canvas.button_press_event(x, y, 1)
        x, y = self.viewer.axes.transData.transform([[30.1, 4]])[0]
        self.viewer.axes.figure.canvas.motion_notify_event(x, y, 1)

        assert_allclose(self.profile_tools.rng_mode.state.x_range, (1.9, 30.1))

        self.profile_tools.ui.button_fit.click()
        self.profile_tools.wait_for_fit()
        process_events()

        world_log = self.profile_tools.text_log.toPlainText().splitlines()
        assert world_log[0] == 'd1'
        assert world_log[1] == 'Coefficients:'
        assert world_log[-2] == '4.000000e+00'
        assert world_log[-1] == '3.500000e+00'

    @requires_pyqt
    def test_fit_settings(self):

        # Regression test for a bug that caused the fit to use a new fitter
        # rather than the one changed in the settings dialog

        self.viewer.add_data(self.data)
        self.profile_tools.ui.tabs.setCurrentIndex(1)
        self.profile_tools.fit_function = PolynomialFitter

        set_degree(self.profile_tools, 1)

        assert fit_coefficients(self.viewer, self.profile_tools) == ['8.000000e+00', '3.500000e+00']

    @requires_pyqt
    def test_fit_settings_per_viewer(self):

        # Each profile viewer keeps its own fitter settings

        viewer2 = self.app.new_data_viewer(ProfileViewer)
        viewer2.state.function = 'mean'
        viewer2.toolbar.active_tool = 'profile-analysis'
        profile_tools2 = viewer2.toolbar.tools['profile-analysis']._profile_tools

        for viewer, profile_tools, degree in [(self.viewer, self.profile_tools, 1),
                                              (viewer2, profile_tools2, 2)]:
            viewer.add_data(self.data)
            profile_tools.ui.tabs.setCurrentIndex(1)
            profile_tools.fit_function = PolynomialFitter
            set_degree(profile_tools, degree)

        assert len(fit_coefficients(self.viewer, self.profile_tools)) == 2
        assert len(fit_coefficients(viewer2, profile_tools2)) == 3

        viewer2.close()

    def test_collapse(self):

        self.viewer.add_data(self.data)

        image_viewer = self.app.new_data_viewer(ImageViewer)
        image_viewer.add_data(self.data)

        self.profile_tools.ui.tabs.setCurrentIndex(2)

        # First try in pixel coordinates

        self.viewer.state.x_att = self.data.pixel_component_ids[0]

        # Force events to be processed to make sure that the callback functions
        # for the computation thread are executed (since they rely on signals)
        self.viewer.layers[0].wait()
        process_events()

        x, y = self.viewer.axes.transData.transform([[0.9, 4]])[0]
        self.viewer.axes.figure.canvas.button_press_event(x, y, 1)
        x, y = self.viewer.axes.transData.transform([[15.1, 4]])[0]
        self.viewer.axes.figure.canvas.motion_notify_event(x, y, 1)

        self.profile_tools.ui.button_collapse.click()

        assert isinstance(image_viewer.state.slices[0], AggregateSlice)
        assert image_viewer.state.slices[0].slice.start == 1
        assert image_viewer.state.slices[0].slice.stop == 15
        assert image_viewer.state.slices[0].center == 0
        assert image_viewer.state.slices[0].function is np.nanmean

        # Next, try in world coordinates

        self.viewer.state.x_att = self.data.world_component_ids[0]

        # Force events to be processed to make sure that the callback functions
        # for the computation thread are executed (since they rely on signals)
        self.viewer.layers[0].wait()
        process_events()

        x, y = self.viewer.axes.transData.transform([[1.9, 4]])[0]
        self.viewer.axes.figure.canvas.button_press_event(x, y, 1)
        x, y = self.viewer.axes.transData.transform([[30.1, 4]])[0]
        self.viewer.axes.figure.canvas.motion_notify_event(x, y, 1)

        self.profile_tools.ui.button_collapse.click()

        assert isinstance(image_viewer.state.slices[0], AggregateSlice)
        assert image_viewer.state.slices[0].slice.start == 1
        assert image_viewer.state.slices[0].slice.stop == 15
        assert image_viewer.state.slices[0].center == 0
        assert image_viewer.state.slices[0].function is np.nanmean

    def test_collapse_reverse(self, capsys):

        # Regression test for a bug that caused collapsing to fail if selecting
        # the range in the reverse direction.

        self.viewer.add_data(self.data)

        image_viewer = self.app.new_data_viewer(ImageViewer)
        image_viewer.add_data(self.data)

        self.profile_tools.ui.tabs.setCurrentIndex(2)

        self.viewer.state.x_att = self.data.pixel_component_ids[0]

        # Force events to be processed to make sure that the callback functions
        # for the computation thread are executed (since they rely on signals)
        self.viewer.layers[0].wait()
        process_events()

        x, y = self.viewer.axes.transData.transform([[15.1, 4]])[0]
        self.viewer.axes.figure.canvas.button_press_event(x, y, 1)
        x, y = self.viewer.axes.transData.transform([[0.9, 4]])[0]
        self.viewer.axes.figure.canvas.motion_notify_event(x, y, 1)

        self.profile_tools.ui.button_collapse.click()
        process_events()

        #  We use capsys here because the # error is otherwise only apparent in stderr.
        out, err = capsys.readouterr()
        assert out.strip() == ""
        assert err.strip() == ""
