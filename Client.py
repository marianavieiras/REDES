import socket
import threading
import tkinter as tk
from tkinter import messagebox

HOST = "192.168.2.126"
PORT = 2004

class ReflexGameClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Duelo de Reflexos")
        self.root.geometry("400x400")
        self.root.configure(bg="lightgray")

        # Nome do jogador
        self.name_label = tk.Label(root, text="Digite seu nome:", font=("Arial", 12), bg="lightgray")
        self.name_label.pack(pady=5)
        self.name_entry = tk.Entry(root, font=("Arial", 12))
        self.name_entry.pack(pady=5)

        self.start_button = tk.Button(root, text="Conectar", font=("Arial", 12), bg="green", fg="white", command=self.connect_to_server)
        self.start_button.pack(pady=5)

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

        # Botão para enviar resposta
        self.button = tk.Button(root, text="Enviar", font=("Arial", 14), bg="blue", fg="white", command=self.send_response)
        self.button.pack(pady=10)
        self.button.config(state="disabled")  # Inicialmente desabilitado

        # Indicador de pontuação
        self.score_label = tk.Label(root, text="Pontuação: 0", font=("Arial", 14), bg="lightgray")
        self.score_label.pack(pady=10)

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
        self.root.after(0, self.label.config, {"text": "Conexão perdida...", "fg": "red"})

    def process_message(self, message):
        """Processa a mensagem recebida e atualiza a interface."""
        if message.startswith("PALAVRA: "):
            # O servidor enviou uma nova palavra
            word = message.split(": ")[1]
            self.word_label.config(text=f"{word}")

        elif "acertou!" in message or "Pontuação:" in message:
            # Atualiza a pontuação dos jogadores
            self.score_label.config(text=message)

        elif "Jogo encerrado!" in message:
            # Exibe o vencedor e encerra o jogo
            self.label.config(text=message, fg="green", font=("Arial", 16, "bold"))
            self.client_socket.close()
            self.is_connected = False

        else:
            # Outras mensagens
            self.label.config(text=message)

    def on_close(self):
        """Fecha a conexão quando a janela é fechada."""
        if self.is_connected and self.client_socket:
            self.client_socket.close()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReflexGameClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()