# chatgpt_qt_with_logs_and_thread.py
# Requisitos: pip install PyQt5 requests
import sys
import os
import json
import datetime
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QPushButton, QAction, QMenuBar, QMessageBox,
    QProgressBar, QFileDialog
)
from PyQt5.QtCore import QThread, pyqtSignal

# >>> Substitui pela tua chave da OpenAI
API_KEY = "AQUI_A_TUA_CHAVE"
API_URL = "https://api.openai.com/v1/chat/completions"
# -----------------------------------------------------


class ApiWorker(QThread):
    """Executa a chamada à API em thread separada e devolve o resultado via signal."""
    result = pyqtSignal(object)

    def __init__(self, api_key, api_url, payload, timeout=30):
        super().__init__()
        self.api_key = api_key
        self.api_url = api_url
        self.payload = payload
        self.timeout = timeout

    def run(self):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            resp = requests.post(self.api_url, headers=headers, json=self.payload, timeout=self.timeout)

            if resp.ok:
                try:
                    j = resp.json()
                except Exception:
                    # resposta não JSON
                    self.result.emit({"ok": False, "error": f"Resposta inválida do servidor: {resp.text}"})
                    return

                # tenta extrair conteúdo de forma robusta
                content = None
                choices = j.get("choices")
                if isinstance(choices, list) and len(choices) > 0:
                    first = choices[0]
                    if isinstance(first, dict):
                        # chat models: first["message"]["content"]
                        msg = first.get("message")
                        if isinstance(msg, dict) and "content" in msg:
                            content = msg["content"]
                        # fallback: completion text
                        elif "text" in first:
                            content = first.get("text")

                if content is None:
                    # fallback para mostrar algo útil
                    content = json.dumps(j, ensure_ascii=False, indent=2)

                self.result.emit({"ok": True, "content": content})
            else:
                # tenta detalhar erro da API
                try:
                    err = resp.json()
                except Exception:
                    err = resp.text
                self.result.emit({"ok": False, "error": f"HTTP {resp.status_code}: {err}"})

        except Exception as e:
            self.result.emit({"ok": False, "error": str(e)})


class ChatGPTApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatGPT API - Qt App (corrigido)")
        self.setGeometry(200, 200, 800, 700)

        # Mensagens (lista no formato: {"role": "...", "content": "..."})
        self.messages = []

        # Logs automáticos com timestamp
        agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_json = os.path.abspath(f"conversa_{agora}.json")
        self.log_txt = os.path.abspath(f"conversa_{agora}.txt")

        # UI
        self._build_menu()
        self._build_central()

        # Worker (inicialmente nenhum)
        self.worker = None

    def _build_menu(self):
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu("Ficheiro")
        help_menu = self.menu_bar.addMenu("Ajuda")

        self.action_clear = QAction("Limpar conversa", self)
        self.action_clear.triggered.connect(self.clear_conversation)
        file_menu.addAction(self.action_clear)

        self.action_import = QAction("Importar conversa JSON", self)
        self.action_import.triggered.connect(self.import_conversation)
        file_menu.addAction(self.action_import)

        self.action_export_json = QAction("Exportar conversa JSON", self)
        self.action_export_json.triggered.connect(self.export_conversation)
        file_menu.addAction(self.action_export_json)

        self.action_export_txt = QAction("Exportar conversa TXT", self)
        self.action_export_txt.triggered.connect(self.export_conversation_txt)
        file_menu.addAction(self.action_export_txt)

        file_menu.addSeparator()

        self.action_exit = QAction("Sair", self)
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)

        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _build_central(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Escreve a tua mensagem...")
        self.input_text.setFixedHeight(110)
        self.layout.addWidget(self.input_text)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.get_response)
        self.layout.addWidget(self.send_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminado
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

    def add_message(self, role, content, write_log=True):
        """Adiciona à lista de mensagens e escreve nos logs (JSON sobrescreve, TXT acrescenta)."""
        entry = {"role": role, "content": content}
        self.messages.append(entry)

        if write_log:
            # JSON (sobrescreve com todo o histórico)
            try:
                with open(self.log_json, "w", encoding="utf-8") as f:
                    json.dump(self.messages, f, ensure_ascii=False, indent=4)
            except Exception as e:
                # não bloqueia a execução; mostra aviso no chat
                self.chat_display.append(f"⚠️ Não foi possível gravar log JSON: {e}")

            # TXT (apende)
            try:
                with open(self.log_txt, "a", encoding="utf-8") as f:
                    prefix = "Tu" if role == "user" else "ChatGPT"
                    f.write(f"{prefix}: {content}\n\n")
            except Exception as e:
                self.chat_display.append(f"⚠️ Não foi possível gravar log TXT: {e}")

    def render_messages(self):
        """Renderiza o histórico completo no display (limpa e reescreve)."""
        self.chat_display.clear()
        for msg in self.messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                self.chat_display.append(f"🧑 Tu: {content}\n")
            elif role == "assistant":
                self.chat_display.append(f"🤖 ChatGPT: {content}\n")
            else:
                # mostra roles desconhecidos de forma neutra
                self.chat_display.append(f"{role}: {content}\n")

    def set_ui_busy(self, busy: bool):
        """Activa/desactiva controlos enquanto uma request está em curso."""
        self.send_button.setEnabled(not busy)
        self.action_import.setEnabled(not busy)
        self.action_export_json.setEnabled(not busy)
        self.action_export_txt.setEnabled(not busy)
        self.action_clear.setEnabled(not busy)
        self.progress_bar.setVisible(busy)

    def get_response(self):
        """Inicia o pedido ao ChatGPT (executado em thread)."""
        pergunta = self.input_text.toPlainText().strip()
        if not pergunta:
            QMessageBox.warning(self, "Aviso", "Escreve uma mensagem primeiro!")
            return

        if not API_KEY or API_KEY == "AQUI_A_TUA_CHAVE":
            QMessageBox.critical(self, "Erro", "Por favor configura a variável API_KEY no script antes de enviar.")
            return

        # 1) adiciona mensagem do utilizador ao histórico e grava
        self.add_message("user", pergunta)

        # 2) mostra o histórico actualizado e limpa a caixa
        self.render_messages()
        self.input_text.clear()

        # 3) mostra indicador temporário de escrita (UI busy)
        self.chat_display.append("🤖 ChatGPT está a escrever...\n")
        self.set_ui_busy(True)

        # 4) prepara payload e worker
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": self.messages,
            "max_tokens": 400,
            "temperature": 0.7
        }

        self.worker = ApiWorker(API_KEY, API_URL, payload, timeout=30)
        self.worker.result.connect(self.on_worker_result)
        self.worker.start()

    def on_worker_result(self, result):
        """Recebe resultado do worker (sucesso ou erro)."""
        self.set_ui_busy(False)

        if result.get("ok"):
            content = result.get("content", "")
            # adiciona resposta ao histórico (e grava)
            self.add_message("assistant", content)
            # re-renderiza o histórico (remove o placeholder)
            self.render_messages()
        else:
            error = result.get("error", "Erro desconhecido")
            # remove placeholder re-renderizando (não adiciona ao histórico)
            # mostra erro no ecrã
            self.chat_display.append(f"⚠️ Erro: {error}\n")
            # também mostra uma caixa para chamar a atenção
            QMessageBox.critical(self, "Erro na API", str(error))

        # limpa referência ao worker
        self.worker = None

    def clear_conversation(self):
        """Limpa apenas o histórico em memória e display; não remove ficheiros já escritos."""
        self.messages = []
        self.chat_display.clear()
        self.chat_display.append("🔄 Conversa limpa.\n")

    def import_conversation(self):
        """Importa um ficheiro JSON com o histórico e passa a gravar nesse ficheiro."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Importar Conversa", "", "JSON Files (*.json);;All Files (*)")
        if not file_name:
            return

        try:
            with open(file_name, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            if not isinstance(loaded, list):
                raise ValueError("O ficheiro JSON não contém uma lista de mensagens.")

            # valida os elementos básicos (role + content)
            for item in loaded:
                if not isinstance(item, dict) or "role" not in item or "content" not in item:
                    raise ValueError("Formato inválido: cada item deve ter 'role' e 'content'.")

            # substitui o histórico atual pelo importado
            self.messages = loaded

            # passa a gravar no mesmo ficheiro importado (com suporte TXT paralelo)
            self.log_json = os.path.abspath(file_name)
            base, _ = os.path.splitext(self.log_json)
            self.log_txt = base + ".txt"

            self.render_messages()
            QMessageBox.information(self, "Importar", "Conversa importada com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao importar: {e}")

    def export_conversation(self):
        """Exporta o histórico para um ficheiro JSON escolhido."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Exportar Conversa JSON", "", "JSON Files (*.json)")
        if not file_name:
            return
        if not file_name.lower().endswith(".json"):
            file_name += ".json"
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Exportar", "Conversa exportada com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar: {e}")

    def export_conversation_txt(self):
        """Exporta o histórico para ficheiro TXT legível."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Exportar Conversa TXT", "", "Text Files (*.txt)")
        if not file_name:
            return
        if not file_name.lower().endswith(".txt"):
            file_name += ".txt"
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                for msg in self.messages:
                    prefix = "Tu" if msg.get("role") == "user" else ("ChatGPT" if msg.get("role") == "assistant" else msg.get("role"))
                    f.write(f"{prefix}: {msg.get('content','')}\n\n")
            QMessageBox.information(self, "Exportar", "Conversa exportada para TXT com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar TXT: {e}")

    def show_about(self):
        QMessageBox.information(self, "Sobre",
                                "Aplicação ChatGPT com PyQt5 (corrigido)\n"
                                "Inclui histórico, logs JSON/TXT, import/export, e execução em thread.\n"
                                "Funciona em Windows, Ubuntu e macOS.")

    # Override closeEvent para garantir que thread termina
    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            # tenta parar worker educadamente (não ideal, mas avisa o utilizador)
            QMessageBox.warning(self, "Atenção", "Uma requisição está em curso. Fecha a aplicação novamente para forçar.")
            # primeiramente não fecha para evitar corromper ficheiros; se o utilizador insistir, deixa fechar
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ChatGPTApp()
    win.show()
    sys.exit(app.exec_())
