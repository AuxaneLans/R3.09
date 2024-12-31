# === Client Python (PyQt6) ===
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTextEdit
)
from PyQt6.QtCore import QTimer
import socket

class ClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Client - Envoi de Programme Multilangage")
        
        # Initialisation des widgets
        self.label_file = QLabel("Fichier à envoyer :")
        self.text_file = QLineEdit()
        self.text_file.setReadOnly(True)
        self.button_browse = QPushButton("Parcourir")
        self.label_ip = QLabel("Adresse IP du serveur :")
        self.text_ip = QLineEdit("127.0.0.1")
        self.label_port = QLabel("Port :")
        self.text_port = QLineEdit("5000")
        self.label_lang = QLabel("Langage :")
        self.text_lang = QLineEdit("python")  # Par défaut "python"
        self.button_send = QPushButton("Envoyer")
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)

        # Layout
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.label_file)
        file_layout.addWidget(self.text_file)
        file_layout.addWidget(self.button_browse)

        server_layout = QHBoxLayout()
        server_layout.addWidget(self.label_ip)
        server_layout.addWidget(self.text_ip)
        server_layout.addWidget(self.label_port)
        server_layout.addWidget(self.text_port)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(self.label_lang)
        lang_layout.addWidget(self.text_lang)

        main_layout = QVBoxLayout()
        main_layout.addLayout(file_layout)
        main_layout.addLayout(server_layout)
        main_layout.addLayout(lang_layout)
        main_layout.addWidget(self.button_send)
        main_layout.addWidget(QLabel("Résultat :"))
        main_layout.addWidget(self.result_area)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Connexions
        self.button_browse.clicked.connect(self.browse_file)
        self.button_send.clicked.connect(self.send_file)

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier", "", "Tous les fichiers (*)")
        if file_name:
            self.text_file.setText(file_name)

    def send_file(self):
        file_path = self.text_file.text()
        server_ip = self.text_ip.text()
        server_port = self.text_port.text()
        language = self.text_lang.text().strip().lower()

        if not file_path or not server_ip or not server_port or not language:
            self.result_area.append("Veuillez remplir tous les champs.")
            return

        try:
            server_port = int(server_port)
        except ValueError:
            self.result_area.append("Le port doit être un nombre valide.")
            return

        try:
            with open(file_path, 'r') as file:
                program_data = file.read()

            # Connexion au serveur
            self.result_area.append("Connexion au serveur...")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, server_port))

            # Envoi des données
            self.result_area.append("Envoi du programme...")
            payload = f"{language}\n{program_data}"
            client_socket.sendall(payload.encode('utf-8'))

            # Réception de la réponse
            response = client_socket.recv(4096).decode('utf-8')
            self.result_area.append(f"Réponse du serveur :\n{response}")

            client_socket.close()
        except FileNotFoundError:
            self.result_area.append("Fichier introuvable.")
        except ConnectionRefusedError:
            self.result_area.append("Connexion refusée. Vérifiez l'adresse IP et le port.")
        except Exception as e:
            self.result_area.append(f"Erreur : {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClientGUI()
    window.show()
    sys.exit(app.exec())
