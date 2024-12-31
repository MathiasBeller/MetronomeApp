import sys
import os
import sqlite3
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSlider, QLineEdit, QComboBox, QHBoxLayout, QPushButton, QInputDialog, QTextEdit, QGroupBox, QListWidget, QListWidgetItem
from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtGui import QIntValidator, QIcon  # Correct import for QIntValidator and QIcon

class MetronomeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metronome")
        self.setGeometry(100, 100, 600, 600)
        
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
        self.first_beat_sound_selector = QComboBox(self)  # Initialize first_beat_sound_selector
        self.populate_sound_selector()
        self.sound_selector.currentIndexChanged.connect(self.update_sound)
        self.first_beat_sound_selector.currentIndexChanged.connect(self.update_sound)

        self.playlist_selector = QComboBox(self)
        self.populate_playlist_selector()
        self.playlist_selector.currentIndexChanged.connect(self.load_playlist)

        self.song_name_input = QLineEdit(self)
        self.song_name_input.setPlaceholderText("Enter song name")

        self.bpm_input = QLineEdit(self)
        self.bpm_input.setPlaceholderText("Enter BPM")
        self.bpm_input.setValidator(QIntValidator(30, 240))  # Only allow integers between 30 and 240

        self.taktart_input = QComboBox(self)
        self.taktart_input.addItems(["3/4", "4/4", "5/4", "6/8"])

        self.add_song_button = QPushButton("Add Song", self)
        self.add_song_button.clicked.connect(self.add_song)

        self.save_playlist_button = QPushButton("Save Playlist", self)
        self.save_playlist_button.clicked.connect(self.save_playlist)

        self.load_playlist_button = QPushButton("Load Playlist", self)
        self.load_playlist_button.clicked.connect(self.load_playlist)

        self.show_db_button = QPushButton("Show Database", self)
        self.show_db_button.clicked.connect(self.show_database)

        # Load icons
        play_icon = QIcon(os.path.join(os.path.dirname(__file__), "play.png"))
        stop_icon = QIcon(os.path.join(os.path.dirname(__file__), "stop.png"))

        self.start_button = QPushButton(self)
        self.start_button.setIcon(play_icon)
        self.start_button.clicked.connect(self.start_metronome)

        self.stop_button = QPushButton(self)
        self.stop_button.setIcon(stop_icon)
        self.stop_button.clicked.connect(self.stop_metronome)

        self.db_display = QTextEdit(self)
        self.db_display.setReadOnly(True)

        self.playlist_display = QListWidget(self)
        self.playlist_display.itemClicked.connect(self.song_clicked)

        self.beat_layout = QHBoxLayout()
        self.beat_labels = []

        # GroupBox for current settings
        settings_group = QGroupBox("Current Settings")
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self.bpm_display)
        settings_layout.addWidget(self.slider)

        # Add labels and combo boxes to the settings layout
        settings_layout.addWidget(QLabel("Time Signature:"))
        settings_layout.addWidget(self.taktart_selector)
        settings_layout.addWidget(QLabel("Sound:"))
        settings_layout.addWidget(self.sound_selector)
        settings_layout.addWidget(QLabel("First Beat Sound:"))
        settings_layout.addWidget(self.first_beat_sound_selector)
        settings_layout.addWidget(self.start_button)
        settings_layout.addWidget(self.stop_button)
        settings_layout.addLayout(self.beat_layout)
        settings_group.setLayout(settings_layout)

        # GroupBox for database information
        db_group = QGroupBox("Database Information")
        db_layout = QVBoxLayout()
        db_layout.addWidget(self.playlist_selector)
        db_layout.addWidget(self.song_name_input)
        db_layout.addWidget(self.bpm_input)
        db_layout.addWidget(self.taktart_input)
        db_layout.addWidget(self.add_song_button)
        db_layout.addWidget(self.save_playlist_button)
        db_layout.addWidget(self.load_playlist_button)
        db_layout.addWidget(self.show_db_button)
        db_layout.addWidget(self.playlist_display)
        db_layout.addWidget(self.db_display)
        db_group.setLayout(db_layout)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(settings_group)
        main_layout.addWidget(db_group)
        container = QWidget()
        container.setLayout(main_layout)
        
        self.setCentralWidget(container)
        
        self._bpm = 60
        self._taktart = "4/4"
        self._beat_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_label)
        self.timer.start(60000 // self._bpm)

        self.update_taktart(0)  # Initialize beat labels

        self.sound = QSoundEffect()
        self.first_beat_sound = QSoundEffect()
        self.update_sound(0)  # Initialize sound

        self.current_playlist = []

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

    def add_song(self):
        song_name = self.song_name_input.text()
        bpm = self.bpm_input.text()
        taktart = self.taktart_input.currentText()
        if song_name and bpm:
            self.current_playlist.append((song_name, bpm, taktart))
            self.update_playlist_display()

    def update_playlist_display(self):
        self.playlist_display.clear()
        for song in self.current_playlist:
            item = QListWidgetItem(f"Name: {song[0]}, BPM: {song[1]}, Taktart: {song[2]}")
            item.setData(Qt.UserRole, song)
            self.playlist_display.addItem(item)

    def save_playlist(self):
        playlist_name, ok = QInputDialog.getText(self, 'Save Playlist', 'Enter playlist name:')
        if ok and playlist_name:
            self.cursor.execute('INSERT INTO playlists (name) VALUES (?)', (playlist_name,))
            playlist_id = self.cursor.lastrowid
            for song in self.current_playlist:
                self.cursor.execute('''
                    INSERT INTO songs (playlist_id, name, bpm, time_signature)
                    VALUES (?, ?, ?, ?)
                ''', (playlist_id, song[0], song[1], song[2]))
            self.conn.commit()
            self.populate_playlist_selector()
            self.current_playlist = []
            self.update_playlist_display()

    def load_playlist(self):
        playlist_name = self.playlist_selector.currentText()
        self.cursor.execute('SELECT id FROM playlists WHERE name = ?', (playlist_name,))
        playlist_id = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT name, bpm, time_signature FROM songs WHERE playlist_id = ?', (playlist_id,))
        songs = self.cursor.fetchall()
        self.current_playlist = [(song[0], song[1], song[2]) for song in songs]
        self.update_playlist_display()

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
                self.first_beat_sound_selector.addItem(name_without_extension)
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

        first_beat_sound_name = self.first_beat_sound_selector.currentText()
        first_beat_sound_file = self.sound_files[first_beat_sound_name]
        self.first_beat_sound.setSource(QUrl.fromLocalFile(first_beat_sound_file))
        self.first_beat_sound.setVolume(1.0)  # Set volume to 100%

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
            label.setFixedSize(100, 100)  # Set fixed size for the labels
            if i == 0:
                label.setStyleSheet("background-color: white; font-size: 24px; border: 2px solid red;")  # Emphasize first beat
            else:
                label.setStyleSheet("background-color: white; font-size: 24px;")
            self.beat_layout.addWidget(label)
            self.beat_labels.append(label)

    def update_label(self):
        self._beat_count += 1
        beats = int(self._taktart.split('/')[0])
        if self._beat_count > beats:
            self._beat_count = 1

        for i, label in enumerate(self.beat_labels):
            if i == self._beat_count - 1:
                if i == 0:
                    label.setStyleSheet("background-color: red;")  # Flash effect for first beat
                    self.first_beat_sound.play()
                else:
                    label.setStyleSheet("background-color: blue;")  # Flash effect for other beats
                    self.sound.play()
            else:
                if i == 0:
                    label.setStyleSheet("background-color: white; border: 2px solid red;")  # Reset first beat
                else:
                    label.setStyleSheet("background-color: white;")

    def song_clicked(self, item):
        song = item.data(Qt.UserRole)
        self.song_name_input.setText(song[0])
        self.bpm_input.setText(str(song[1]))  # Convert BPM to string
        self.taktart_input.setCurrentText(song[2])
        self.slider.setValue(int(song[1]))
        self.taktart_selector.setCurrentText(song[2])

    def start_metronome(self):
        self.timer.start(60000 // self._bpm)

    def stop_metronome(self):
        self.timer.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetronomeApp()
    window.show()
    sys.exit(app.exec())