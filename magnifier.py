#!/usr/bin/env python
import sys
import signal
from PySide6.QtCore import QObject, Slot, Qt, QTimer, QPoint, QLoggingCategory
from PySide6.QtCore import QtMsgType, qCDebug
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QGuiApplication, QCursor, QPainter


lc = QLoggingCategory("com.kyzivat.magnifier", QtMsgType.QtWarningMsg)
lctimer = QLoggingCategory("com.kyzivat.magnifier.timer", QtMsgType.QtWarningMsg)


class ZoomWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        #self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)

        self._zoom_label = QLabel(self)
        self._layout.addWidget(self._zoom_label)

        self._long_interval = 1000
        self._short_interval = 32
        self._no_move_count = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._updateZoomPixmap)
        self._timer.start(self._short_interval)
        self._last_screen_pos = None
        self.setGeometry(0, 0, 500, 500)

    def enterEvent(self, event):
        qCDebug(lc, "enterEvent")
        #self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)

    def leaveEvent(self, event):
        qCDebug(lc, "leaveEvent")
        #self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

    def paintEvent(self, event):
        if lc.isDebugEnabled():
            painter = QPainter(self)
            painter.setPen(Qt.white)
            pen_width = painter.pen().width()
            painter.drawRect(0, 0, self.width()-pen_width, self.height()-pen_width)
        super().paintEvent(event)

    def _updateTimerInterval(self, cursor_pos):
        if self._last_screen_pos == cursor_pos:
            if lctimer.isDebugEnabled():
                print(".", end="")
                sys.stdout.flush()
            if self._timer.interval != self._long_interval:
                self._no_move_count += 1
            if self._no_move_count > self._long_interval / self._short_interval:
                self._timer.setInterval(self._long_interval)
        else:
            if lctimer.isDebugEnabled():
                backspaces = "\b" * (self._no_move_count)
                spaces = " " * (self._no_move_count)
                print(backspaces + spaces + backspaces, end="")
                sys.stdout.flush()
            if self._timer.interval() != self._short_interval:
                self._timer.setInterval(self._short_interval)
            self._no_move_count = 0

        self._last_screen_pos = cursor_pos

    @Slot()
    def _updateZoomPixmap(self):
        global_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(global_pos)
        if screen is None:
            return

        screen_pos = screen.geometry().topLeft()
        local_pos = global_pos - screen_pos
        if self._last_screen_pos == local_pos:
            self._updateTimerInterval(local_pos)
            return
        self._updateTimerInterval(local_pos)

        grabsize = self._zoom_label.size()/3
        pixmap = screen.grabWindow(0, local_pos.x()-grabsize.width()/2,
                                   local_pos.y()-grabsize.height()/2, grabsize.width(),
                                   grabsize.height())
        scaled_pixmap = pixmap.scaled(self._zoom_label.size()*screen.devicePixelRatio())
        self._zoom_label.setPixmap(scaled_pixmap)
        qCDebug(lc, f"grabsize: {grabsize}, pixmap: {pixmap.size()}, scaled_pixmap: {scaled_pixmap.size()}, label size: {self._zoom_label.size()}")


def sigint_handler(signal, frame):
    qApp.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    app = QApplication(sys.argv)

    window = ZoomWindow()
    window.show()

    sys.exit(app.exec())

