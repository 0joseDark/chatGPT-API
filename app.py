import sys
import requests
import json
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QPushButton, QAction, QMenuBar, QMessageBox,
    QProgressBar, QFileDialog
)


# ⚠️ Coloca aqui a tua chave da API
API_KEY = "AQUI_A_TUA_CHAVE"
API_URL = "https://api.openai.com/v1/chat/completions"


class ChatGPTApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configurações da janela
        self.setWindowTitle("ChatGPT API - Qt App (com histórico, logs e import/export)")
        self.setGeometry(200, 200, 750, 650)

        # Histórico de mensagens (para enviar à API)
        self.messages = []

        # Nome do ficheiro log automático
        agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_json = f"conversa_{agora}.json"
        self.log_txt = f"conversa_{agora}.txt"

        # Menu
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu("Ficheiro")
        help_menu = self.menu_bar.addMenu("Ajuda")

        clear_action = QAction("Limpar conversa", self)
        clear_action.triggered.connect(self.clear_conversation)
        file_menu.addAction(clear_action)

        import_action = QAction("Importar conversa JSON", self)
        import_action.triggered.connect(self.import_conversation)
        file_menu.addAction(import_action)

        export_action = QAction("Exportar conversa JSON", self)
        export_action.triggered.connect(self.export_conversation)
        file_menu.addAction(export_action)

        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Área central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Caixa para mostrar conversa
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        # Caixa para escrever pergunta
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Escreve a tua mensagem...")
        self.input_text.setFixedHeight(100)
        self.layout.addWidget(self.input_text)

        # Botão Enviar
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.get_response)
        self.layout.addWidget(self.send_button)

        # Barra de progresso (indeterminada)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

    def log_message(self, role, content):
        """ Guarda a conversa em ficheiros JSON e TXT """
        entry = {"role": role, "content": content}

        # Atualiza JSON automático
        self.messages.append(entry)
        with open(self.log_json, "w", encoding="utf-8") as f_json:
            json.dump(self.messages, f_json, ensure_ascii=False, indent=4)

        # Atualiza TXT automático
        with open(self.log_txt, "a", encoding="utf-8") as f_txt:
            prefix = "Tu" if role == "user" else "ChatGPT"
            f_txt.write(f"{prefix}: {content}\n\n")

    def get_response(self):
        """ Envia a mensagem para a API e mostra a resposta no histórico """
        pergunta = self.input_text.toPlainText().strip()

        if not pergunta:
            QMessageBox.warning(self, "Aviso", "Escreve uma mensagem primeiro!")
            return

        # Mostra no chat e guarda no log
        self.chat_display.append(f"🧑 Tu: {pergunta}\n")
        self.log_message("user", pergunta)

        # Limpa a caixa de entrada
        self.input_text.clear()

        # Mostra indicador de "a escrever..."
        self.chat_display.append("🤖 ChatGPT está a escrever...\n")
        self.progress_bar.setVisible(True)
        self.repaint()

        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "gpt-3.5-turbo",
                "messages": self.messages,
                "max_tokens": 300
            }

            response = requests.post(API_URL, headers=headers, json=data)

            if response.status_code == 200:
                resposta = response.json()["choices"][0]["message"]["content"]

                # Adiciona resposta ao histórico
                self.chat_display.append(f"🤖 ChatGPT: {resposta}\n")
                self.log_message("assistant", resposta)

            else:
                erro = f"Erro {response.status_code}: {response.text}"
                self.chat_display.append(f"⚠️ {erro}\n")

        except Exception as e:
            self.chat_display.append(f"⚠️ Erro de conexão: {str(e)}\n")

        finally:
            self.progress_bar.setVisible(False)

    def clear_conversation(self):
        """ Limpa o histórico da conversa (apenas no display, não apaga ficheiros) """
        self.messages = []
        self.chat_display.clear()
        self.chat_display.append("🔄 Conversa limpa.\n")

    def import_conversation(self):
        """ Importa conversa de um ficheiro JSON """
        file_name, _ = QFileDialog.getOpenFileName(self, "Importar Conversa", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, "r", encoding="utf-8") as f:
                    self.messages = json.load(f)

                self.chat_display.clear()
                for msg in self.messages:
                    prefix = "🧑 Tu" if msg["role"] == "user" else "🤖 ChatGPT"
                    self.chat_display.append(f"{prefix}: {msg['content']}\n")

                QMessageBox.information(self, "Importar", "Conversa importada com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao importar: {e}")

    def export_conversation(self):
        """ Exporta conversa para ficheiro JSON escolhido pelo utilizador """
        file_name, _ = QFileDialog.getSaveFileName(self, "Exportar Conversa", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(self.messages, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Exportar", "Conversa exportada com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar: {e}")

    def show_about(self):
        QMessageBox.information(self, "Sobre",
                                "Aplicação ChatGPT com PyQt5\n"
                                "Inclui histórico, barra de progresso, logs e import/export JSON.\n"
                                "Compatível com Windows, Ubuntu e macOS.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatGPTApp()
    window.show()
    sys.exit(app.exec_())
