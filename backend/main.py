from fastapi import FastAPI, Query
from database import init_db, HistoricoBusca, Feedback
from pydantic import BaseModel
from transformers import pipeline
from spotipy.oauth2 import SpotifyClientCredentials
from tortoise.transactions import in_transaction
from tortoise.expressions import Q
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from collections import Counter
from fastapi.responses import JSONResponse
from fastapi.middleware import CORSMiddleware
import random
import spotipy
from dotenv import load_dotenv
import os

# Criando a API
app = FastAPI()

# Inicializar Banco de Dados PostgreSQL
init_db(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que o frontend faça requisições de qualquer origem
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def analisar_sentimento_bert(texto):
    resultado = sentiment_analysis(texto)
    label = resultado[0]['label']

    palavras_raiva = ["raiva", "irritado", "puto", "ódio", "furioso", "bravo", "explodindo"]
    palavras_tristeza = ["triste", "deprimido", "chorar", "angustiado", "sofrendo", "melancólico"]
    palavras_felicidade = ["feliz", "alegre", "contente", "animado", "empolgado", "sorrindo"]
    palavras_neutras = ["neutro", "indiferente", "tanto faz", "normal", "ok"]
    palavras_motivacao = ["motivado", "determinado", "focado", "vencer", "disciplinado"]
    palavras_nostalgia = ["nostalgia", "saudade", "lembrança", "recordação", "passado"]
    
    # 🔥 Verificar feedbacks corrigidos antes de retornar um sentimento
    feedback_corrigido = await Feedback.filter(sentimento_detectado=texto).first()
    if feedback_corrigido:
        return feedback_corrigido.sentimento_corrigido  # Usa a correção do usuário!
    
    # 🔥 Verifica palavras-chave no texto digitado
    texto_lower = texto.lower()

    if any(palavra in texto_lower for palavra in palavras_raiva):
        return "Raiva 😡"
    elif any(palavra in texto_lower for palavra in palavras_tristeza):
        return "Negativo 😢"
    elif any(palavra in texto_lower for palavra in palavras_felicidade):
        return "Positivo 😀"
    elif any(palavra in texto_lower for palavra in palavras_neutras):
        return "Neutro 😐"
    elif any(palavra in texto_lower for palavra in palavras_motivacao):
        return "Motivação 💪"
    elif any(palavra in texto_lower for palavra in palavras_nostalgia):
        return "Nostalgia 🕰️"

    if "1" in label or "2" in label:
        return "Negativo 😢"
    elif "3" in label:
        return "Neutro 😐"
    elif "4" in label or "5" in label:
        return "Positivo 😀"

    return "Indefinido 🤔"

# Endpoint para análise de sentimento
@app.post("/analisar_sentimento/")
def analisar_sentimento(dados: TextoEntrada):
    sentimento = analisar_sentimento_bert(dados.texto)
    return {"sentimento": sentimento}

# Função para recomendar playlists com base no sentimento
async def recomendar_playlist(sentimento):
    categorias = {
        "Positivo 😀": ["Happy", "Good Vibes", "Energia", "Alegria"],
        "Negativo 😢": ["Sad", "Tristeza", "Depressivo", "Chorar"],
        "Neutro 😐": ["Chill", "Relax", "Lo-Fi", "Ambient"],
        "Raiva 😡": ["Rock Pesado", "Metal", "Rap Revoltado", "Hardcore", "Furia"]
    }

    # 🔥 Se houver feedback corrigindo um sentimento, usar a versão corrigida
    feedback_corrigido = await Feedback.filter(sentimento_detectado=sentimento).first()
    if feedback_corrigido and feedback_corrigido.sentimento_corrigido:
        sentimento = feedback_corrigido.sentimento_corrigido
        
    palavras_chave = categorias.get(sentimento, ["Chill"])
    query = " OR ".join(palavras_chave)

    try:
        print(f"🔎 Buscando playlists para: {query}")  
        results = sp.search(q=query, type="playlist", limit=20)  

        print(f"📌 Resposta da API do Spotify: {results}")  

        if results and "playlists" in results and results["playlists"]:
            playlists = results["playlists"].get("items", [])

            playlists = [
                {
                    "nome": p.get("name", "Desconhecido"),
                    "id": p.get("id"),
                    "image": p["images"][0]["url"] if p.get("images") else "https://via.placeholder.com/300",
                    "seguidores": p["followers"]["total"] if "followers" in p else 0
                }
                for p in playlists if p and p.get("id") and p.get("name")
            ]

            playlists.sort(key=lambda x: x["seguidores"], reverse=True)

            if playlists:
                playlist_escolhida = random.choice(playlists[:5])  
                print(f"✅ Playlist escolhida: {playlist_escolhida}")  
                return playlist_escolhida

        return {"erro": "Nenhuma playlist válida encontrada, tente novamente."}

    except Exception as e:
        print(f"⚠️ Erro ao buscar playlists: {e}")  
        return {"erro": str(e)}

# Endpoint para recomendar playlists baseado no sentimento
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

# 🔥 Lista de palavras-chave aprendidas com feedback
palavras_personalizadas = {
    "Raiva 😡": [],
    "Negativo 😢": [],
    "Positivo 😀": [],
    "Neutro 😐": []
}

def ajustar_palavras_chave(sentimento_errado, sentimento_correto):
    """
    Ajusta a classificação de sentimentos com base nos feedbacks recebidos.
    Se um erro for corrigido muitas vezes, ele será adicionado como nova palavra-chave para o sentimento correto.
    """
    if sentimento_correto in palavras_personalizadas:
        palavras_personalizadas[sentimento_correto].append(sentimento_errado.lower())

    print(f"🔥 Ajuste de palavras-chave: {palavras_personalizadas}")

@app.post("/feedback/")
async def receber_feedback(dados: dict):
    sentimento_atual = dados.get("sentimento")
    confirmado = dados.get("confirmado")
    correcao = dados.get("correcao")
    
    if not sentimento_atual:
        return {"erro": "Sentimento não informado."}
    
    sentimento_corrigido = sentimento_atual if confirmado else correcao

    await Feedback.create(
        sentimento_detectado=sentimento_atual,
        sentimento_corrigido=sentimento_corrigido,
        confirmado=confirmado
    )

    # 🔥 Se houver muitas correções para o mesmo sentimento, substituímos a palavra-chave original!
    if not confirmado:
        correcao_count = await Feedback.filter(sentimento_detectado=sentimento_atual, confirmado=False).count()
        if correcao_count >= 3:  # Se houver muitas correções, alterar a lógica de palavras-chave!
            ajustar_palavras_chave(sentimento_atual, sentimento_corrigido)

    return {"mensagem": "Feedback salvo com sucesso! Obrigado por contribuir!"}

@app.get("/", response_class=HTMLResponse)
def home(request: Request): 
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/historico/")
async def listar_historico(
    sentimento: str = Query(None, description="Filtrar por sentimento (Positivo, Neutro, Negativo)"),
    limite: int = Query(10, description="Número máximo de registros a retornar")
):
    """ Retorna o histórico de buscas armazenado no banco de dados. """
    try:
        # Se um sentimento for passado, filtra os registros
        filtros = Q()
        if sentimento:
            filtros &= Q(sentimento=sentimento)

        historico = await HistoricoBusca.filter(filtros).limit(limite).order_by("-id")

        return [
            {
                "texto_digitado": item.texto_digitado,
                "sentimento": item.sentimento,
                "playlist_nome": item.playlist_nome,
                "playlist_id": item.playlist_id,
                "link": f"https://open.spotify.com/playlist/{item.playlist_id}"
            }
            for item in historico
        ]

    except Exception as e:
        return {"erro": str(e)}

@app.get("/estatisticas/")
async def obter_estatisticas():
    historico = await HistoricoBusca.all()
    sentimentos = [busca.sentimento for busca in historico]

    contagem = Counter(sentimentos)

    return JSONResponse(content={
        "Positivo 😀": contagem.get("Positivo 😀", 0),
        "Negativo 😢": contagem.get("Negativo 😢", 0),
        "Neutro 😐": contagem.get("Neutro 😐", 0),
        "Raiva 😡": contagem.get("Raiva 😡", 0)
    })

@app.get("/estatisticas_feedback/")
async def estatisticas_feedback():
    feedbacks = await Feedback.all()
    
    total = len(feedbacks)
    confirmados = sum(1 for f in feedbacks if f.confirmado)
    corrigidos = total - confirmados

    return {"Confirmados": confirmados, "Corrigidos": corrigidos}

# Configuração para servir a interface web
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")