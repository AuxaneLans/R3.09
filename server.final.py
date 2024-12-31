import socket
import threading
import subprocess
import os
import re

# Variable globale pour garder une trace des clients connectés
connected_clients = 0
lock = threading.Lock()

def handle_client(client_socket, client_address):
    global connected_clients
    print(f"Connexion acceptée de {client_address}")
    try:
        # Réception des données envoyées par le client
        data = client_socket.recv(4096).decode('utf-8')
        if not data:
            client_socket.sendall("Aucun programme reçu.".encode('utf-8'))
            return

        # Le client envoie le langage en première ligne, suivi du programme
        lines = data.split('\n', 1)
        if len(lines) < 2:
            client_socket.sendall("Format invalide : Langage non spécifié.".encode('utf-8'))
            return

        language, program_data = lines[0].strip().lower(), lines[1]

        # Écriture du programme reçu dans un fichier temporaire
        temp_filename = "temp_program"
        if language == "python":
            temp_filename += ".py"
        elif language == "java":
            temp_filename += ".java"
        else:
            client_socket.sendall(f"Langage non supporté : {language}".encode('utf-8'))
            return

        with open(temp_filename, "w", encoding="utf-8") as temp_file:
            temp_file.write(program_data)

        # Code permettant l'exécution du programme selon le langage
        try:
            if language == "python":
                result = subprocess.run(
                    ["python3", temp_filename], capture_output=True, text=True
                )
            elif language == "java":
                # Extraire le nom de la classe publique
                with open(temp_filename, "r", encoding="utf-8") as temp_file:
                    content = temp_file.read()
                match = re.search(r'public\s+class\s+(\w+)', content)
                if not match:
                    client_socket.sendall("Erreur : Impossible de trouver une classe publique dans le fichier Java.".encode('utf-8'))
                    return

                class_name = match.group(1)
                java_filename = f"{class_name}.java"
                os.rename(temp_filename, java_filename)

                # Compiler le fichier Java
                compile_result = subprocess.run(
                    ["javac", java_filename], capture_output=True, text=True
                )
                if compile_result.returncode != 0:
                    client_socket.sendall(compile_result.stderr.encode('utf-8'))
                    return

                # Exécuter le programme Java
                result = subprocess.run(
                    ["java", class_name], capture_output=True, text=True
                )

                # Supprimer les fichiers générés
                os.remove(java_filename)
                class_file = f"{class_name}.class"
                if os.path.exists(class_file):
                    os.remove(class_file)
            else:
                client_socket.sendall(f"Langage non supporté : {language}".encode('utf-8'))
                return

            # Envoi des résultats au client
            if result.returncode == 0:
                client_socket.sendall(result.stdout.encode('utf-8'))
            else:
                client_socket.sendall(result.stderr.encode('utf-8'))
        except Exception as e:
            client_socket.sendall(f"Erreur lors de l'exécution : {str(e)}".encode('utf-8'))
        finally:
            # Suppression du fichier temporaire
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    except Exception as e:
        print(f"Erreur avec le client {client_address} : {str(e)}")
        client_socket.sendall(f"Erreur : {str(e)}".encode('utf-8'))
    finally:
        client_socket.close()
        print(f"Connexion fermée avec {client_address}")
        with lock:
            connected_clients -= 1  # retire un client à chaque socket fermé

def start_server(host, port):
    global connected_clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Serveur démarré sur {host}:{port}")

    while True:
        try:
            client_socket, client_address = server_socket.accept()

            with lock:
                if connected_clients >= 2:  # Limite de clients connectés
                    client_socket.sendall("Trop de clients connectés. Réessayez plus tard.".encode('utf-8'))
                    client_socket.close()
                    continue

                connected_clients += 1  # ajoute un client à chaque socket ouvert

            client_thread = threading.Thread(
                target=handle_client, args=(client_socket, client_address)
            )
            client_thread.start()
        except KeyboardInterrupt:
            print("Arrêt du serveur...")
            server_socket.close()
            break
        except Exception as e:
            print(f"Erreur du serveur : {str(e)}")

if __name__ == "__main__":
    # Demander l'adresse IP et le port à l'utilisateur
    host = input("Entrez l'adresse IP pour le serveur (par défaut: 0.0.0.0) : ") or "0.0.0.0"
    port = input("Entrez le port pour le serveur (par défaut: 5000) : ")

    try:
        port = int(port) if port else 5000
        start_server(host, port)
    except ValueError:
        print("Le port doit être un nombre entier valide.")
