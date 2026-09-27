"""Regression tests for the icon navigation button."""

import pytest

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from src.xianjue.ui.nav_button import NAV_ICONS


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.mark.parametrize("svg", NAV_ICONS.values())
def test_nav_icons_render_visible_pixels(qapp, svg):
    rendered = svg.replace("__COLOR__", "#70B0FF")
    pixmap = QPixmap(64, 64)
    pixmap.fill(0)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(rendered.encode("utf-8")).render(painter, QRectF(0, 0, 64, 64))
    painter.end()

    image = pixmap.toImage()
    visible_pixels = sum(
        image.pixelColor(x, y).alpha() > 0
        for x in range(8, 56)
        for y in range(8, 56)
    )
    assert visible_pixels > 0
