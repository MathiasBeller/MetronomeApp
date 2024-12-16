import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSlider, QLineEdit
from PySide6.QtCore import QTimer, Qt

class MetronomeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metronome")
        self.setGeometry(100, 100, 300, 200)
        
        self.label = QLabel("Metronome", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.bpm_display = QLineEdit(self)
        self.bpm_display.setReadOnly(True)
        self.bpm_display.setAlignment(Qt.AlignCenter)
        self.bpm_display.setText("60 BPM")
        
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(30, 240)  # BPM range
        self.slider.setValue(60)       # Default BPM
        self.slider.valueChanged.connect(self.update_bpm)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.bpm_display)
        container = QWidget()
        container.setLayout(layout)
        
        self.setCentralWidget(container)
        
        self._bpm = 60
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_label)
        self.timer.start(60000 // self._bpm)

    def update_bpm(self, value):
        self._bpm = value
        self.bpm_display.setText(f"{self._bpm} BPM")
        self.timer.setInterval(60000 // self._bpm)

    def update_label(self):
        self.label.setText("Beat!")
        self.label.setStyleSheet("background-color: blue;")  # Flash effect
        QTimer.singleShot(100, self.reset_label)

    def reset_label(self):
        self.label.setText("Metronome")
        self.label.setStyleSheet("background-color: white;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetronomeApp()
    window.show()
    sys.exit(app.exec())