from unittest.mock import MagicMock, patch

from echo import CallbackProperty
from qtpy import QtGui

from ..colors import qt_to_mpl_color, QColorBox, connect_color, QColormapCombo, cmap2pixmap


def test_colors():
    assert qt_to_mpl_color(QtGui.QColor(255, 0, 0)) == '#ff0000'
    assert qt_to_mpl_color(QtGui.QColor(255, 255, 255)) == '#ffffff'


# TODO: add a test for the other way around

# TODO: add a test for cmap2pixmap

# TODO: add a test for tint_pixmap

def test_color_box():

    func = MagicMock()

    label = QColorBox()
    label.resize(100, 100)
    label.colorChanged.connect(func)
    label.setColor('#472822')

    assert func.call_count == 1


def test_connect_color():

    class FakeClass(object):
        color = CallbackProperty()

    c = FakeClass()

    label = QColorBox()

    connect_color(c, 'color', label)

    label.setColor('#472822')

    assert c.color == '#472822'

    c.color = '#012345'

    assert label.color() == '#012345'


def test_colormap_combo():

    combo = QColormapCombo()


def test_colormap_combo_icon_cache():

    # A second combo should reuse the images rendered for the first one
    # rather than render them again, whatever its width.

    combo1 = QColormapCombo()

    with patch('glue_qt.utils.colors.cmap2pixmap', wraps=cmap2pixmap) as render:
        combo2 = QColormapCombo()
        combo2.resize(combo1.width() + 10, combo1.height())
        combo2._update_icons()

    assert render.call_count == 0
    assert combo2.itemIcon(0).availableSizes() == [combo2.iconSize()]
