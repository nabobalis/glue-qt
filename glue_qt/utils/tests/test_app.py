import subprocess
import sys


def test_import_does_not_import_qtquick():
    # QtQuick is slow to import and only needed by get_qapp under Qt6, so
    # importing the module should not import it. We check this in a
    # subprocess since other tests may already have imported it.
    code = "import sys, glue_qt.utils.app; assert 'qtpy.QtQuick' not in sys.modules"
    subprocess.check_call([sys.executable, '-c', code])
