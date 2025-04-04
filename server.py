import socket
import threading
import random
import tkinter as tk
from tkinter import messagebox
import time

HOST = "0.0.0.0"
PORT = 2003

# Lista de palavras que serão enviadas
WORDS = ["Servidor", "Reflexo", "Pacote", "Dispositivo", "Comunicação", "Transporte", "Aplicação", "Confiabilidade", "Conexão", "Protocolo", "Firewall", "Varredura", "Ethernet"]

clients = {}
scores = {}
current_word = ""

def accept_connections(server_socket, update_ui_callback):
    """Aceita conexões de jogadores."""
    while True:
        update_ui_callback()
        client_socket, addr = server_socket.accept()
        nickname = client_socket.recv(1024).decode("utf-8").strip()
        clients[nickname] = client_socket
        scores[nickname] = 0

        print(f"Conexão de {addr} com o nome {nickname}")
        print(f"Client Socket: {client_socket}\n")

        broadcast(f"{nickname} entrou no jogo!")
        update_ui_callback()

        threading.Thread(target=handle_client, args=(client_socket, nickname, update_ui_callback)).start()

def broadcast(message):
    """Envia uma mensagem para todos os clientes conectados."""
    if not clients:
        return
    for client in clients.values():
        try:
            client.sendall(message.encode("utf-8"))
        except Exception as e:
            print("\33[31mErro ao enviar broadcast:\33[0m \n", e) 

def handle_client(client_socket, nickname, update_ui_callback):
    """Gerencia a interação com cada jogador."""
    global current_word

    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                break

            if message == "disconnect_client":
                broadcast(f"{nickname} saiu do jogo.")
                clients[nickname].close()
                if nickname in clients:
                    del clients[nickname]
                break
        
            if message == "request_connected_players":
                connected_players = ", ".join(clients.keys())
                client_socket.sendall(f"Jogadores conectados: {connected_players}".encode("utf-8"))
                continue

            if message.strip().lower() == current_word.lower():
                scores[nickname] += 1
                broadcast(f"{nickname} acertou!")
                update_ui_callback()   
                # Broadcast da pontuação       
                scores_message = "Pontos: " + ", ".join([f"{player} - {score}" for player, score in scores.items()])
                broadcast(scores_message) 
                time.sleep(1)
                start_new_round(update_ui_callback)

                # Se alguém atingir 5 pontos, o jogo acaba
                if scores[nickname] >= 5:
                    broadcast(f"Jogo encerrado! Vencedor: {nickname}")
                    time.sleep(2)
                    for client in clients.values():
                        print(f"Encerrando conexão de {client}...")
                        client.close()
                    clients.clear()
                    scores.clear()
                    update_ui_callback()  
                    break
            elif message.strip():  # Verifica se a mensagem não está vazia
                # Envia "Palavra incorreta" apenas para tentativas de resposta
                client_socket.sendall("Palavra incorreta! Tente novamente.".encode("utf-8"))
        except Exception as e:
            print(f"Erro com {nickname}: {e}")
            break
    update_ui_callback()

def start_new_round(update_ui_callback):
    """Escolhe uma nova palavra e avisa os jogadores."""
    global current_word

    countdown_seconds = 3
    while countdown_seconds > 0:
        if any(score == 5 for score in scores.values()):
            return
        broadcast(f"Próxima palavra em {countdown_seconds} segundos...")
        countdown_seconds -= 1
        time.sleep(1)
    current_word = random.choice(WORDS)
    broadcast(f"PALAVRA: {current_word}")
    update_ui_callback()  

class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Servidor - Jogo de Reflexos")
        self.root.geometry("500x500")

        self.label = tk.Label(root, text="Servidor rodando...", font=("Arial", 14, 'bold'))
        self.label.pack(pady=10)

        self.start_button = tk.Button(root, text="Iniciar Jogo", font=("Arial", 12), command=self.start_game)
        self.start_button.pack(pady=10)

        self.users_label = tk.Label(root, text="Usuários conectados:", font=("Arial", 12))
        self.users_label.pack(pady=10)

        self.users_list = tk.Listbox(root, font=("Arial", 12), height=10)
        self.users_list.pack(pady=10, fill=tk.BOTH, expand=True)

        self.current_word_label = tk.Label(root, text="Palavra atual: -", font=("Arial", 12))
        self.current_word_label.pack(pady=10)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reutilização da porta 2003
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()

        threading.Thread(target=self.accept_connections_thread, daemon=True).start()

    def accept_connections_thread(self):
        """Thread para aceitar conexões."""
        accept_connections(self.server_socket, self.update_ui)
        #update_connected_players()

    def update_ui(self):
        """Atualiza a interface com os usuários conectados e a palavra atual."""
        self.users_list.delete(0, tk.END)
        for nickname in clients.keys():
            self.users_list.insert(tk.END, f"{nickname} - Pontos: {scores[nickname]}")
        self.current_word_label.config(text=f"Palavra atual: {current_word if current_word else '-'}")

        if len(clients) == 0:
            self.label.config(text='Servidor rodando...', fg='black', font=('Arial', 14, 'bold'))

    def start_game(self):
        """Inicia uma nova rodada manualmente."""
        if not clients:
            messagebox.showwarning("Aviso", "Nenhum jogador conectado!")
            return
        elif len(clients) < 2:
            messagebox.showwarning("Aviso", "É necessário pelo menos 2 jogadores para iniciar o jogo!")
            return
        
        self.label.config(text='Jogo iniciado!', fg='green', font=('Arial', 14, "bold"))
        self.users_list.delete(0, tk.END)

        #update_connected_players()
        start_new_round(self.update_ui)

    def on_close(self):
        """Fecha o servidor e encerra as conexões."""
        for client in clients.values():
            client.close()
        self.server_socket.close()
        self.root.destroy()
        print("\33[41mServidor encerrado.\33[0m")

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()