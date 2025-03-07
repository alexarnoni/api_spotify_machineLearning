from fastapi import FastAPI
from database import init_db, HistoricoBusca, Feedback
from pydantic import BaseModel
from transformers import pipeline
from spotipy.oauth2 import SpotifyClientCredentials
from tortoise.transactions import in_transaction
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from collections import Counter
import random
import spotipy
from dotenv import load_dotenv
import os

# ✅ Criando a API
app = FastAPI()

# ✅ Inicializar Banco de Dados PostgreSQL
init_db(app)

# ✅ Configurar CORS (permitir requisições do frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir qualquer frontend se conectar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Inicializando modelo de análise de sentimentos (BERT)
sentiment_analysis = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# ✅ Carregar variáveis do .env
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))

# ✅ Servir arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ✅ Modelo para entrada de dados
class TextoEntrada(BaseModel):
    texto: str

# ✅ Função para análise de sentimentos
async def analisar_sentimento_bert(texto):
    # 🔥 Verificar feedbacks corrigidos antes de retornar um sentimento
    feedback_corrigido = await Feedback.filter(sentimento_detectado=texto).first()
    if feedback_corrigido:
        return feedback_corrigido.sentimento_corrigido  # Usa a correção do usuário!

    resultado = sentiment_analysis(texto)
    label = resultado[0]['label']

    # 🔥 Dicionário de palavras-chave para sentimentos específicos
    categorias_sentimentos = {
        "Raiva 😡": ["raiva", "irritado", "puto", "ódio", "furioso", "bravo", "explodindo"],
        "Negativo 😢": ["triste", "deprimido", "chorar", "angustiado", "sofrendo", "melancólico"],
        "Positivo 😀": ["feliz", "alegre", "contente", "animado", "empolgado", "sorrindo"],
        "Neutro 😐": ["neutro", "indiferente", "tanto faz", "normal", "ok"],
        "Motivação 💪": ["motivado", "determinado", "focado", "vencer", "disciplinado"],
        "Nostalgia 🕰️": ["nostalgia", "saudade", "lembrança", "recordação", "passado"]
    }

    # 🔥 Verifica palavras-chave no texto digitado
    texto_lower = texto.lower()
    for sentimento, palavras in categorias_sentimentos.items():
        if any(palavra in texto_lower for palavra in palavras):
            return sentimento

    # 🔥 Se não encontrar palavras-chave, usa a classificação BERT
    if "1" in label or "2" in label:
        return "Negativo 😢"
    elif "3" in label:
        return "Neutro 😐"
    elif "4" in label or "5" in label:
        return "Positivo 😀"

    return "Indefinido 🤔"

# ✅ Endpoint para análise de sentimento
@app.post("/analisar_sentimento/")
async def analisar_sentimento(dados: TextoEntrada):
    sentimento = await analisar_sentimento_bert(dados.texto)
    return {"sentimento": sentimento}

# ✅ Função para recomendar playlists com base no sentimento
async def recomendar_playlist(sentimento):
    categorias = {
        "Positivo 😀": ["Happy", "Good Vibes", "Energia", "Alegria"],
        "Negativo 😢": ["Sad", "Tristeza", "Depressivo", "Chorar"],
        "Neutro 😐": ["Chill", "Relax", "Lo-Fi", "Ambient"],
        "Raiva 😡": ["Rock Pesado", "Metal", "Rap Revoltado", "Hardcore", "Furia"]
    }

    palavras_chave = categorias.get(sentimento, ["Chill"])
    query = " OR ".join(palavras_chave)

    try:
        results = sp.search(q=query, type="playlist", limit=20)
        playlists = results["playlists"].get("items", [])

        playlists_validas = [
            {
                "nome": p.get("name", "Desconhecido"),
                "id": p.get("id"),
                "image": p["images"][0]["url"] if p.get("images") else "https://via.placeholder.com/300"
            }
            for p in playlists if p and p.get("id") and p.get("name")
        ]

        if playlists_validas:
            return random.choice(playlists_validas[:5])

    except Exception as e:
        return {"erro": str(e)}

    return {"erro": "Nenhuma playlist válida encontrada, tente novamente."}

# ✅ Endpoint para recomendar playlists baseado no sentimento
@app.post("/recomendar_playlist/")
async def recomendar(dados: TextoEntrada):
    sentimento = await analisar_sentimento_bert(dados.texto)
    playlist_escolhida = await recomendar_playlist(sentimento)

    if "erro" not in playlist_escolhida:
        async with in_transaction():
            await HistoricoBusca.create(
                texto_digitado=dados.texto,
                sentimento=sentimento,
                playlist_nome=playlist_escolhida["nome"],
                playlist_id=playlist_escolhida["id"]
            )

        return {"sentimento": sentimento, "playlist_recomendada": playlist_escolhida}

    return {"erro": "Nenhuma playlist encontrada."}

# ✅ Endpoint para exibir a página inicial (frontend)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ✅ Endpoint para estatísticas de sentimentos
@app.get("/estatisticas/")
async def obter_estatisticas():
    historico = await HistoricoBusca.all()
    contagem = Counter(busca.sentimento for busca in historico)

    return JSONResponse(content=contagem)

# ✅ Endpoint para estatísticas de feedbacks
@app.get("/estatisticas_feedback/")
async def estatisticas_feedback():
    feedbacks = await Feedback.all()
    return {"Confirmados": sum(f.confirmado for f in feedbacks), "Corrigidos": len(feedbacks)}

