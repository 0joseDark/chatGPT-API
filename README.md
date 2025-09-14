# chatGPT-API
- API, Application Programming Interface

# 📌 1. O que precisamos

1. **Python 3.8+**
2. **Bibliotecas**:

   * `PyQt5` (interface gráfica)
   * `requests` (para fazer chamadas HTTP à API do ChatGPT)
3. **Chave da API da OpenAI** (precisas criar uma conta no [OpenAI](https://platform.openai.com/) e obter a tua chave).

No terminal instalamos:

```bash
pip install PyQt5 requests
```

---

# 📌 2. Estrutura da aplicação

A aplicação terá:

* Uma **janela Qt**.
* Uma **caixa de texto** onde escreves a pergunta.
* Um **botão "Enviar"** que chama a API do ChatGPT.
* Uma **área de saída** que mostra a resposta do modelo.
* Um **menu** com opções básicas: Sair, Limpar, Sobre.

---

# 📌 3. Código da API + Qt

```python
import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QPushButton, QLabel, QAction, QMenuBar, QMessageBox
)

# ⚠️ Coloca aqui a tua chave da API
API_KEY = "AQUI_A_TUA_CHAVE"
API_URL = "https://api.openai.com/v1/chat/completions"


class ChatGPTApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configurações da janela
        self.setWindowTitle("ChatGPT API - Qt App")
        self.setGeometry(200, 200, 600, 500)

        # Menu
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu("Ficheiro")
        help_menu = self.menu_bar.addMenu("Ajuda")

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

        # Campo para escrever pergunta
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Escreve a tua pergunta para o ChatGPT...")
        self.layout.addWidget(self.input_text)

        # Botão Enviar
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.get_response)
        self.layout.addWidget(self.send_button)

        # Área de resposta
        self.output_label = QLabel("Resposta do ChatGPT aparecerá aqui.")
        self.output_label.setWordWrap(True)
        self.layout.addWidget(self.output_label)

    def get_response(self):
        """ Envia a pergunta para a API do ChatGPT e mostra a resposta """
        pergunta = self.input_text.toPlainText().strip()

        if not pergunta:
            QMessageBox.warning(self, "Aviso", "Escreve uma pergunta primeiro!")
            return

        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": pergunta}],
                "max_tokens": 200
            }

            response = requests.post(API_URL, headers=headers, json=data)

            if response.status_code == 200:
                resposta = response.json()["choices"][0]["message"]["content"]
                self.output_label.setText(resposta)
            else:
                self.output_label.setText(f"Erro: {response.status_code}\n{response.text}")

        except Exception as e:
            self.output_label.setText(f"Erro de conexão: {str(e)}")

    def show_about(self):
        QMessageBox.information(self, "Sobre", "Aplicação ChatGPT com PyQt5\nCompatível com Windows, Ubuntu e macOS.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatGPTApp()
    window.show()
    sys.exit(app.exec_())
```

---

# 📌 4. Como funciona

1. O utilizador escreve uma **pergunta** no campo de texto.
2. Clica no botão **Enviar**.
3. O programa envia um **pedido HTTP POST** para a API do ChatGPT (`/v1/chat/completions`).
4. A resposta em JSON é lida e mostrada no **label** da janela.
5. O menu permite **sair** ou ver **informações**.

---

# 📌 5. Comentários importantes

* **API\_KEY** → substitui `"AQUI_A_TUA_CHAVE"` pela tua chave verdadeira.
* Funciona em **Windows 10, Ubuntu e macOS** sem alterações (Qt é multiplataforma).
* Podes trocar `"gpt-3.5-turbo"` por `"gpt-4o-mini"` se tiveres acesso.
* É possível melhorar o layout: colocar a resposta numa `QTextEdit` para suportar textos longos.

---


