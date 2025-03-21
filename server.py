import socket
import threading
import random
import tkinter as tk
from tkinter import messagebox

HOST = "192.168.2.126"
PORT = 2004

# Lista de palavras que serão enviadas
WORDS = ["Python", "Reflexo", "Código", "Computador", "Jogador", "Desafio", "Rápido", "Digitando", "Vencedor"]

clients = {}
scores = {}
current_word = ""

def broadcast(message):
    """Envia uma mensagem para todos os clientes conectados."""
    for client in clients.values():
        try:
            client.sendall(message.encode("utf-8"))
        except:
            pass  # Ignorar erros ao enviar mensagens

def handle_client(client_socket, nickname, update_ui_callback):
    """Gerencia a interação com cada jogador."""
    global current_word

    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                break

            if message.strip().lower() == current_word.lower():
                # Primeiro jogador a acertar pontua
                scores[nickname] += 1
                broadcast(f"{nickname} acertou! Pontuação: {scores[nickname]}")
                update_ui_callback()  # Atualiza a interface com as pontuações

                # Se alguém atingir 5 pontos, o jogo acaba
                if scores[nickname] >= 5:
                    broadcast(f"Jogo encerrado! Vencedor: {nickname}")
                    break

                # Escolher nova palavra e enviar para todos
                start_new_round(update_ui_callback)

        except Exception as e:
            print(f"Erro com {nickname}: {e}")
            break

    client_socket.close()
    del clients[nickname]
    del scores[nickname]
    broadcast(f"{nickname} saiu do jogo.")
    update_ui_callback()  # Atualiza a interface com os usuários restantes

def start_new_round(update_ui_callback):
    """Escolhe uma nova palavra e avisa os jogadores."""
    global current_word
    current_word = random.choice(WORDS)
    broadcast(f"PALAVRA: {current_word}")
    update_ui_callback()  # Atualiza a interface com a nova palavra

def accept_connections(server_socket, update_ui_callback):
    """Aceita conexões de jogadores."""
    while True:
        client_socket, addr = server_socket.accept()
        client_socket.sendall("Digite seu nome: ".encode("utf-8"))
        nickname = client_socket.recv(1024).decode("utf-8").strip()

        clients[nickname] = client_socket
        scores[nickname] = 0

        print(f"{nickname} entrou no jogo!")
        broadcast(f"{nickname} entrou no jogo!")
        update_ui_callback()  # Atualiza a interface com os novos usuários

        threading.Thread(target=handle_client, args=(client_socket, nickname, update_ui_callback)).start()

class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Servidor - Jogo de Reflexos")
        self.root.geometry("400x400")

        self.label = tk.Label(root, text="Servidor rodando...", font=("Arial", 14))
        self.label.pack(pady=10)

        self.start_button = tk.Button(root, text="Iniciar Jogo", font=("Arial", 12), command=self.start_game)
        self.start_button.pack(pady=10)

        self.users_label = tk.Label(root, text="Usuários conectados:", font=("Arial", 12))
        self.users_label.pack(pady=10)

        self.users_list = tk.Listbox(root, font=("Arial", 12), height=10)
        self.users_list.pack(pady=10, fill=tk.BOTH, expand=True)

        self.current_word_label = tk.Label(root, text="Palavra atual: Nenhuma", font=("Arial", 12))
        self.current_word_label.pack(pady=10)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()

        threading.Thread(target=self.accept_connections_thread, daemon=True).start()

    def accept_connections_thread(self):
        """Thread para aceitar conexões."""
        accept_connections(self.server_socket, self.update_ui)

    def update_ui(self):
        """Atualiza a interface com os usuários conectados e a palavra atual."""
        self.users_list.delete(0, tk.END)
        for nickname in clients.keys():
            self.users_list.insert(tk.END, f"{nickname} - Pontos: {scores[nickname]}")
        self.current_word_label.config(text=f"Palavra atual: {current_word if current_word else 'Nenhuma'}")

    def start_game(self):
        """Inicia uma nova rodada manualmente."""
        if not clients:
            messagebox.showwarning("Aviso", "Nenhum jogador conectado!")
            return
        start_new_round(self.update_ui)

    def on_close(self):
        """Fecha o servidor e encerra as conexões."""
        for client in clients.values():
            client.close()
        self.server_socket.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()