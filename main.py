from fastapi import FastAPI
from database import init_db, HistoricoBusca
from pydantic import BaseModel
from transformers import pipeline
from spotipy.oauth2 import SpotifyClientCredentials
from tortoise.transactions import in_transaction
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import random
import spotipy
from dotenv import load_dotenv
import os

# Criando a API
app = FastAPI()

# Inicializar Banco de Dados PostgreSQL
init_db(app)

# Inicializando modelo de análise de sentimentos (BERT)
sentiment_analysis = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# Carregar variáveis do .env
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                           client_secret=SPOTIPY_CLIENT_SECRET))

# Modelo para entrada de dados
class TextoEntrada(BaseModel):
    texto: str

# Função para análise de sentimentos
def analisar_sentimento_bert(texto):
    resultado = sentiment_analysis(texto)
    label = resultado[0]['label']

    if "1" in label or "2" in label:
        return "Negativo 😢"
    elif "3" in label:
        return "Neutro 😐"
    elif "4" in label or "5" in label:
        return "Positivo 😀"
    else:
        return "Indefinido 🤔"

# Endpoint para análise de sentimento
@app.post("/analisar_sentimento/")
def analisar_sentimento(dados: TextoEntrada):
    sentimento = analisar_sentimento_bert(dados.texto)
    return {"sentimento": sentimento}

# Função para recomendar playlists com base no sentimento
def recomendar_playlist(sentimento):
    categorias = {
        "Positivo 😀": "Happy",
        "Negativo 😢": "Sad",
        "Neutro 😐": "Chill"
    }

    categoria = categorias.get(sentimento, "Chill")

    try:
        print(f"🔎 Buscando playlists para: {categoria}")  # DEBUG
        results = sp.search(q=categoria, type="playlist", limit=10)

        print(f"📌 Resposta completa da API do Spotify: {results}")  # DEBUG

        if results and "playlists" in results and results["playlists"]:
            playlists = results["playlists"].get("items", [])

            # 🔥 NOVO: Remover valores None da lista
            playlists = [p for p in playlists if p is not None]

            if not playlists:
                print("❌ Nenhuma playlist válida encontrada.")  # DEBUG
                return {"erro": "Nenhuma playlist encontrada, tente novamente."}

            # Filtrar apenas playlists com nome e ID válidos
            playlists_validas = [
                {"nome": p.get("name", "Desconhecido"), "id": p.get("id")}
                for p in playlists if p.get("id") and p.get("name")
            ]

            if playlists_validas:
                playlist_escolhida = random.choice(playlists_validas)
                print(f"✅ Playlist escolhida: {playlist_escolhida}")  # DEBUG
                return playlist_escolhida

        return {"erro": "Nenhuma playlist válida encontrada, tente novamente."}

    except Exception as e:
        print(f"⚠️ Erro ao buscar playlists: {e}")  # DEBUG
        return {"erro": str(e)}
    
# Endpoint para recomendar playlists baseado no sentimento
@app.post("/recomendar_playlist/")
async def recomendar(dados: TextoEntrada):
    sentimento = analisar_sentimento_bert(dados.texto)
    playlist_escolhida = recomendar_playlist(sentimento)

    if "erro" not in playlist_escolhida:  # Verifica se a recomendação deu certo
        async with in_transaction():
            await HistoricoBusca.create(
                texto_digitado=dados.texto,
                sentimento=sentimento,
                playlist_nome=playlist_escolhida["nome"],
                playlist_id=playlist_escolhida["id"]
            )

        return {"sentimento": sentimento, "playlist_recomendada": playlist_escolhida}
    
    return {"erro": "Nenhuma playlist encontrada."}

# Configuração para servir a interface web
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
