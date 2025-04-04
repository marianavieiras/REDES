import socket
import threading
import tkinter as tk
from tkinter import messagebox
import time

HOST = "192.168.2.111"
PORT = 2003

class ReflexGameClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Duelo de Reflexos")
        self.root.geometry("600x750")
        self.root.configure(bg="lightgray")
        
        # Nome do jogador
        self.name_label = tk.Label(root, text="Digite seu nome:", font=("Arial", 14), bg="lightgray")
        self.name_label.pack(pady=5)
        self.name_entry = tk.Entry(root, font=("Arial", 12))
        self.name_entry.bind("<Return>", lambda event:self.connect_to_server())
        self.name_entry.pack(pady=5)

        self.start_button = tk.Button(root, text="Conectar", font=("Arial", 12), bg="green", fg="white", command=self.connect_to_server)
        self.start_button.pack(pady=5)

        # Jogadores conectados
        self.connected_players_label = tk.Label(root, text="Jogadores conectados:", font=("Arial", 12), bg="lightgray")
        self.connected_players_label.pack(pady=5)
        self.connected_players_list = tk.Text(root, font=("Arial", 12), height=3, width=20, state="disabled", bg="white")
        self.connected_players_list.pack(pady=5)

        # Botão para atualizar jogadores conectados
        self.update_connected_players_button = tk.Button(root, text="Atualizar Jogadores", font=("Arial", 12), bg="blue", fg="white", command=self.request_connected_players)
        self.update_connected_players_button.pack(pady=5)

        # Mensagem inicial
        self.label = tk.Label(root, text="Aguardando conexão...", font=("Arial", 14), bg="lightgray")
        self.label.pack(pady=10)

        # Palavra a ser digitada
        self.word_label = tk.Label(root, text="...", font=("Arial", 18, "bold"), fg="red", bg="white", width=20, height=2)
        self.word_label.pack(pady=10)

        # Campo de entrada para resposta
        self.entry = tk.Entry(root, font=("Arial", 14))
        self.entry.pack(pady=10)
        self.entry.config(state="disabled")  # Inicialmente desabilitado
        self.entry.bind("<Return>", lambda event:self.send_response())

        # Botão para enviar resposta
        self.button = tk.Button(root, text="Enviar", font=("Arial", 14), bg="blue", fg="white", command=self.send_response)
        self.button.pack(pady=10)
        self.button.config(state="disabled")  # Inicialmente desabilitado

        # Mensagem de próxima palavra
        self.next_word_label = tk.Label(root, text="Próxima palavra em: -", font=("Arial", 14), bg="lightgray")
        self.next_word_label.pack(pady=10)

        # Indicador de pontuação
        self.score_label = tk.Label(root, text="Pontuação:", font=("Arial", 14), bg="lightgray")
        self.score_label.pack(pady=10)
        self.score_board = tk.Text(root, font=("Arial", 14), height=6, width=15, state="disabled", bg="white")
        self.score_board.pack(pady=10)

        self.client_socket = None
        self.is_connected = False

    def connect_to_server(self):
        """Conecta ao servidor e envia o nome do jogador."""
        nickname = self.name_entry.get().strip()
        if not nickname:
            messagebox.showwarning("Aviso", "Digite seu nome antes de conectar!")
            return
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client_socket.connect((HOST, PORT))
            self.is_connected = True
            self.client_socket.sendall(nickname.encode("utf-8"))

            # Desabilita o campo de nome e o botão após a conexão
            self.name_entry.config(state="disabled")
            self.start_button.config(state="disabled")
            # Habilita entrada e botão de envio
            self.entry.config(state="normal")
            self.button.config(state="normal")

            self.label.config(text="Aguardando o jogo começar...")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível conectar ao servidor: {e}")
            self.client_socket = None
            self.is_connected = False

    def send_response(self):
        """Envia a resposta para o servidor."""
        response = self.entry.get().strip()
        if response and self.is_connected:
            self.client_socket.sendall(response.encode("utf-8"))
            self.entry.delete(0, tk.END)

    def receive_messages(self):
        """Recebe mensagens do servidor e atualiza a interface."""
        while self.is_connected:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if not message:
                    break
                # Atualiza a interface gráfica na thread principal
                self.root.after(0, self.process_message, message)
            except Exception as e:
                print(f"Erro ao receber mensagem: {e}")
                break

        self.client_socket.close()
        self.is_connected = False

    def request_connected_players(self):
        """Solicita a lista de jogadores conectados ao servidor."""
        if self.is_connected:
            try:
                self.client_socket.sendall("request_connected_players".encode("utf-8"))
            except Exception as e:
                print(f"Erro ao solicitar jogadores conectados: {e}")

    def process_message(self, message):
        """Processa a mensagem recebida e atualiza a interface."""
        if message.startswith("PALAVRA: "):
            word = message.split(": ")[1]
            self.word_label.config(text=f"{word}")

            # Reabilita o campo e o botão de enviar
            self.button.config(state="normal")
            self.entry.config(state="normal")

        elif "entrou no jogo!" in message:
            """Exibe a mensagem de entrada no label principal."""
            self.label.config(text=message, fg="blue", font=("Arial", 14, "bold"))
            player = message.split(" ")[0]
            self.connected_players_list.config(state="normal")
            self.connected_players_list.insert(tk.END, f"{player}\n")

        elif message.startswith("Jogadores conectados: "):
            """Atualiza a lista de jogadores conectados."""
            players = message.split(": ")[1] 
            self.connected_players_list.config(state="normal")
            self.connected_players_list.delete("1.0", tk.END)  
            for player in players.split(", "):  
                self.connected_players_list.insert(tk.END, f"{player}\n")
            self.connected_players_list.config(state="disabled")

        elif "acertou!" in message:
            """Processa a mensagem recebida e atualiza a interface."""
            self.label.config(text=message, fg="blue", font=("Arial", 14, "bold"))
            self.word_label.config(text="...", fg="red", font=("Arial", 18, "bold"))
            
            #Desabilita o campo de digitação e o botão de enviar
            self.button.config(state="disabled")
            self.entry.config(state="disabled")  
        
        elif message.startswith("Palavra incorreta"):
            """Processa a mensagem recebida e atualiza a interface."""
            self.label.config(text=message, fg="red", font=("Arial", 14, "bold"))

        elif "saiu do jogo" in message:
            """Processa a mensagem recebida e atualiza a interface."""
            self.label.config(text=message, fg="red", font=("Arial", 14, "bold"))

        elif "Próxima palavra em" in message:
            """Processa a mensagem recebida e atualiza a interface."""
            self.next_word_label.config(text=message, fg='red', font=("Arial", 14, "bold"))

        elif "Jogo encerrado!" in message:
            """Processa a mensagem recebida e atualiza a interface."""
            self.label.config(text=message, fg="green", font=("Arial", 16, "bold"))
            self.word_label.config(text="...", fg="red", font=("Arial", 18, "bold"))
            self.next_word_label.config(text="Próxima palavra em: -", font=("Arial", 14, "bold"))
            if self.is_connected:
                self.client_socket.close()
                self.is_connected = False
                # Remove os jogadores conectados da lista
                self.connected_players_list.config(state="normal")
                self.connected_players_list.delete("1.0", tk.END)  
                self.connected_players_list.config(state="disabled")

        elif "Pontos:" in message:
            """Processa a mensagem recebida e atualiza a interface."""
            scores = message.split(": ")[1]  
            self.score_board.config(state="normal") 
            self.score_board.delete("1.0", tk.END)  
            for score in scores.split(", "):  
                self.score_board.insert(tk.END, f"{score}\n")  
            self.score_board.config(state="disabled")  
        else:
            """Demais mensagens recebidas."""
            self.label.config(text=message)

    def on_close(self):
        """Fecha a conexão quando a janela é fechada."""
        if self.is_connected and self.client_socket:
            try:
                self.client_socket.sendall("disconnect_client".encode("utf-8"))
            except Exception as e:
                print(f"Erro ao enviar mensagem de desconexão: {e}")
            finally:
                self.client_socket.close()
                print(f"\33[91mConexão de {self.name_entry.get()} encerrada.\33[0m")
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReflexGameClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()