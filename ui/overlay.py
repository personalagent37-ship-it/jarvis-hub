import os

# UI overlay using PyQt6 – displays live transcription and assistant responses.
# Minimalistic, semi‑transparent window with gradient background (hologram style).

from PyQt6 import QtWidgets, QtCore, QtGui

class OverlayWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Thread‑safe queue for messages (list of strings)
        self.message_queue = []
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_messages)
        self.timer.start(200)  # poll every 200 ms

    def init_ui(self):
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(500, 150)
        # Position at bottom‑right of the screen
        screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20, screen.bottom() - self.height() - 20)

        self.label = QtWidgets.QLabel("", self)
        self.label.setStyleSheet(
            "color: #00e5ff; "
            "font: 14pt 'Roboto'; "
            "background: rgba(0,0,0,0.6); "
            "border-radius: 12px; "
            "padding: 8px;"
        )
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        self.label.setWordWrap(True)
        self.label.setGeometry(0, 0, self.width(), self.height())

    def push_message(self, text: str):
        # Called from other threads – store in list, will be displayed on the next timer tick.
        self.message_queue.append(text)

    def update_messages(self):
        if self.message_queue:
            # Keep only the last few messages (max 5) for brevity.
            self.message_queue = self.message_queue[-5:]
            formatted = "\n---\n".join(self.message_queue)
            self.label.setText(formatted)

def start_overlay():
    app = QtWidgets.QApplication([])
    window = OverlayWindow()
    window.show()
    # Run the app event loop in a separate thread – the function returns the window object.
    QtCore.QTimer.singleShot(0, lambda: None)  # ensures the loop starts
    return app, window
