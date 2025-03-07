# 🎵 Recomendador de Playlists - Análise de Sentimentos com FastAPI e Spotify 🎵

## 📌 Sobre o Projeto
Este projeto utiliza **Machine Learning** para **analisar sentimentos** a partir de um texto digitado pelo usuário e recomendar **playlists do Spotify** com base no humor identificado.

✅ **Principais Tecnologias**:
- 🔥 **FastAPI** (Backend)
- 🎵 **Spotify API** (Busca de playlists)
- 🤖 **BERT (Modelo de NLP)** (Análise de sentimentos)
- 🎨 **HTML + CSS + JavaScript** (Interface Web)
- 📊 **Gráficos interativos** (Histórico de buscas e estatísticas de sentimentos)
- 🐘 **PostgreSQL** (Banco de Dados)
  
---

## ⚙️ **Como Rodar o Projeto Localmente?**
### ✅ **1. Clone o Repositório**
```sh
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```
### ✅ 2. Crie um Ambiente Virtual e Instale as Dependências
```sh
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```
 ### 3. Configure as Credenciais do Spotify
 #### 1. Crie um arquivo .env na raiz do projeto e adicione suas credenciais:

 ```sh
SPOTIPY_CLIENT_ID=seu_client_id
SPOTIPY_CLIENT_SECRET=seu_client_secret
DATABASE_URL=postgres://user:senha@host:porta/banco
```
#### 2. Crie as tabelas no banco de dados:
```sh
aerich upgrade
```
### ✅ 4. Execute o Servidor FastAPI
```sh
uvicorn main:app --reload
```
Agora, acesse no navegador:
👉 http://127.0.0.1:8000 (Interface Web)
👉 http://127.0.0.1:8000/docs (Swagger API)

🚀 **Principais Funcionalidades**: 
- ✅ Análise de Sentimento com IA baseada em NLP (BERT).
- ✅ Geração de recomendações automáticas de playlists no Spotify.
- ✅ Dashboard de Estatísticas 📊 com gráficos interativos.
- ✅ Histórico de Pesquisas armazenado no PostgreSQL.

📜 **Licença**
- Este projeto está licenciado sob a MIT License.