import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt, QSize

class PianoKey(QPushButton):
    def __init__(self, is_white=True, parent=None):
        super().__init__(parent)
        self.is_white = is_white
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if self.is_white:
            self.setStyleSheet("background-color: white; border: 1px solid black;")
            self.setFixedSize(24, 160)
        else:
            self.setStyleSheet("background-color: black; border: 1px solid black;")
            self.setFixedSize(16, 100)
            # self.raise_()  # Remove this, will raise after all keys are created

class PianoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ideal Piano")
        self.setMinimumSize(900, 400)
        self.setup_ui()

    def setup_ui(self):
        # Set background image
        palette = QPalette()
        pixmap = QPixmap(900, 400)
        pixmap.loadFromData(self.get_sky_image_bytes())
        palette.setBrush(QPalette.Window, QBrush(pixmap.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # "GO BACK" button
        self.go_back_btn = QPushButton("GO BACK")
        self.go_back_btn.setStyleSheet(
            "background-color: black; color: white; font-size: 16px; border-radius: 8px; padding: 8px 20px;"
        )
        self.go_back_btn.setFixedSize(120, 40)
        self.go_back_btn.setCursor(Qt.PointingHandCursor)

        # Placeholder label
        self.placeholder_label = QLabel("[ ]")
        self.placeholder_label.setStyleSheet("font-size: 18px; color: black;")
        self.placeholder_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Piano keys
        piano_layout = QHBoxLayout()
        piano_layout.setSpacing(0)
        white_key_count = 52
        black_key_pattern = [1, 1, 0, 1, 1, 1, 0]  # C, C#, D, D#, E, F, F#, G, G#, A, A#, B
        black_key_offsets = [0, 1, 3, 4, 5]  # Black keys in an octave (relative to white keys)
        total_keys = 88

        white_keys = []
        black_keys = []

        # Calculate white and black key positions
        white_key_index = 0
        key_positions = []  # Store white key x positions for black key placement
        for i in range(total_keys):
            note_in_octave = i % 12
            if note_in_octave in [0, 2, 4, 5, 7, 9, 11]:  # White keys
                key = PianoKey(is_white=True)
                piano_layout.addWidget(key)
                white_keys.append(key)
                key_positions.append(24 * white_key_index)
                white_key_index += 1

        # After all white keys are added, add black keys as children and raise them
        white_key_index = 0
        for i in range(total_keys):
            note_in_octave = i % 12
            if note_in_octave in [0, 2, 4, 5, 7, 9, 11]:
                white_key_index += 1
            else:  # Black keys
                key = PianoKey(is_white=False, parent=self)
                # Overlay black keys using negative margins
                # Place black key between the previous and current white key
                # The x position is offset from the previous white key
                x = 24 * (white_key_index - 1) + 16
                y = 400 - 160
                key.move(x, y)
                key.show()
                key.raise_()  # Ensure black key is above white keys
                black_keys.append(key)

        # Main layout
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.go_back_btn, alignment=Qt.AlignLeft | Qt.AlignTop)
        top_layout.addSpacing(40)
        top_layout.addWidget(self.placeholder_label, alignment=Qt.AlignLeft | Qt.AlignTop)
        top_layout.addStretch()

        main_layout.addLayout(top_layout)
        main_layout.addStretch()
        main_layout.addLayout(piano_layout)
        self.setLayout(main_layout)

    def get_sky_image_bytes(self):
        # Placeholder: solid color as background, since we can't load external images
        # In a real app, you would load an actual sky image here
        from PIL import Image
        from io import BytesIO
        img = Image.new("RGB", (900, 400), (180, 210, 240))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

def main():
    app = QApplication(sys.argv)
    window = PianoWidget()
    window.show() 
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
