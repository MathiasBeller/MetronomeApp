import sys
import os
import sqlite3
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSlider, QLineEdit, QComboBox, QHBoxLayout, QPushButton, QInputDialog, QTextEdit
from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtMultimedia import QSoundEffect

class MetronomeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metronome")
        self.setGeometry(100, 100, 600, 400)
        
        self.init_db()
        
        self.bpm_display = QLineEdit(self)
        self.bpm_display.setReadOnly(True)
        self.bpm_display.setAlignment(Qt.AlignCenter)
        self.bpm_display.setText("60 BPM")
        
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(30, 240)  # BPM range
        self.slider.setValue(60)       # Default BPM
        self.slider.valueChanged.connect(self.update_bpm)

        self.taktart_selector = QComboBox(self)
        self.taktart_selector.addItems(["3/4", "4/4", "5/4", "6/8"])
        self.taktart_selector.currentIndexChanged.connect(self.update_taktart)

        self.sound_selector = QComboBox(self)
        self.populate_sound_selector()
        self.sound_selector.currentIndexChanged.connect(self.update_sound)

        self.playlist_selector = QComboBox(self)
        self.populate_playlist_selector()
        self.playlist_selector.currentIndexChanged.connect(self.load_playlist)

        self.save_playlist_button = QPushButton("Save Playlist", self)
        self.save_playlist_button.clicked.connect(self.save_playlist)

        self.load_playlist_button = QPushButton("Load Playlist", self)
        self.load_playlist_button.clicked.connect(self.load_playlist)

        self.show_db_button = QPushButton("Show Database", self)
        self.show_db_button.clicked.connect(self.show_database)

        self.db_display = QTextEdit(self)
        self.db_display.setReadOnly(True)

        self.beat_layout = QHBoxLayout()
        self.beat_labels = []

        layout = QVBoxLayout()
        layout.addWidget(self.bpm_display)
        layout.addWidget(self.slider)
        layout.addWidget(self.taktart_selector)
        layout.addWidget(self.sound_selector)
        layout.addWidget(self.playlist_selector)
        layout.addWidget(self.save_playlist_button)
        layout.addWidget(self.load_playlist_button)
        layout.addWidget(self.show_db_button)
        layout.addWidget(self.db_display)
        layout.addLayout(self.beat_layout)
        container = QWidget()
        container.setLayout(layout)
        
        self.setCentralWidget(container)
        
        self._bpm = 60
        self._taktart = "4/4"
        self._beat_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_label)
        self.timer.start(60000 // self._bpm)

        self.update_taktart(0)  # Initialize beat labels

        self.sound = QSoundEffect()
        self.update_sound(0)  # Initialize sound

    def init_db(self):
        self.conn = sqlite3.connect('metronome.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                playlist_id INTEGER,
                name TEXT NOT NULL,
                bpm INTEGER,
                time_signature TEXT,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id)
            )
        ''')
        self.conn.commit()

    def populate_playlist_selector(self):
        self.playlist_selector.clear()
        self.cursor.execute('SELECT name FROM playlists')
        playlists = self.cursor.fetchall()
        for playlist in playlists:
            self.playlist_selector.addItem(playlist[0])

    def save_playlist(self):
        playlist_name, ok = QInputDialog.getText(self, 'Save Playlist', 'Enter playlist name:')
        if ok and playlist_name:
            self.cursor.execute('INSERT INTO playlists (name) VALUES (?)', (playlist_name,))
            playlist_id = self.cursor.lastrowid
            self.cursor.execute('''
                INSERT INTO songs (playlist_id, name, bpm, time_signature)
                VALUES (?, ?, ?, ?)
            ''', (playlist_id, 'Current Song', self._bpm, self._taktart))
            self.conn.commit()
            self.populate_playlist_selector()

    def load_playlist(self):
        playlist_name = self.playlist_selector.currentText()
        self.cursor.execute('SELECT id FROM playlists WHERE name = ?', (playlist_name,))
        playlist_id = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT name, bpm, time_signature FROM songs WHERE playlist_id = ?', (playlist_id,))
        song = self.cursor.fetchone()
        if song:
            self._bpm = song[1]
            self._taktart = song[2]
            self.slider.setValue(self._bpm)
            self.taktart_selector.setCurrentText(self._taktart)
            self.update_bpm(self._bpm)
            self.update_taktart(self.taktart_selector.currentIndex())

    def show_database(self):
        self.cursor.execute('SELECT * FROM playlists')
        playlists = self.cursor.fetchall()
        self.cursor.execute('SELECT * FROM songs')
        songs = self.cursor.fetchall()

        db_content = "Playlists:\n"
        db_content += "ID\tName\n"
        for playlist in playlists:
            db_content += f"{playlist[0]}\t{playlist[1]}\n"

        db_content += "\nSongs:\n"
        db_content += "ID\tPlaylist ID\tName\tBPM\tTime Signature\n"
        for song in songs:
            db_content += f"{song[0]}\t{song[1]}\t{song[2]}\t{song[3]}\t{song[4]}\n"

        self.db_display.setText(db_content)

    def populate_sound_selector(self):
        sound_folder = "C:\\Users\\mathi\\OneDrive\\Coding\\GitHubRepos\\MetronomeApp\\Metronomes"  # Update this path
        self.sound_files = {}
        for file_name in os.listdir(sound_folder):
            if file_name.endswith(".wav"):
                name_without_extension = os.path.splitext(file_name)[0]
                self.sound_selector.addItem(name_without_extension)
                self.sound_files[name_without_extension] = os.path.join(sound_folder, file_name)

    def update_bpm(self, value):
        self._bpm = value
        self.bpm_display.setText(f"{self._bpm} BPM")
        self.timer.setInterval(60000 // self._bpm)

    def update_taktart(self, index):
        self._taktart = self.taktart_selector.currentText()
        self._beat_count = 0
        self.create_beat_labels()

    def update_sound(self, index):
        sound_name = self.sound_selector.currentText()
        sound_file = self.sound_files[sound_name]
        self.sound.setSource(QUrl.fromLocalFile(sound_file))
        self.sound.setVolume(1.0)  # Set volume to 100%

    def create_beat_labels(self):
        # Clear existing labels
        for label in self.beat_labels:
            self.beat_layout.removeWidget(label)
            label.deleteLater()
        self.beat_labels.clear()

        # Create new labels based on the selected time signature
        beats = int(self._taktart.split('/')[0])
        for i in range(beats):
            label = QLabel(f"Beat {i+1}", self)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background-color: white;")
            self.beat_layout.addWidget(label)
            self.beat_labels.append(label)

    def update_label(self):
        self._beat_count += 1
        beats = int(self._taktart.split('/')[0])
        if self._beat_count > beats:
            self._beat_count = 1

        for i, label in enumerate(self.beat_labels):
            if i == self._beat_count - 1:
                label.setStyleSheet("background-color: blue;")  # Flash effect
            else:
                label.setStyleSheet("background-color: white;")

        self.sound.play()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetronomeApp()
    window.show()
    sys.exit(app.exec())