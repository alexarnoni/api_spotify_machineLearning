import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os

# Carregar variáveis do .env
load_dotenv()

# 🔑 Configurar credenciais da API do Spotify
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                           client_secret=SPOTIPY_CLIENT_SECRET))

# Define as palavras-chave para buscar playlists com base no sentimento
def escolher_categoria(sentimento):
    if "Positivo" in sentimento:
        return "Happy"  # Playlist animada
    elif "Negativo" in sentimento:
        return "Sad"  # Playlist triste
    else:
        return "Chill"  # Playlist neutra

# Função para buscar playlists com base no sentimento
def recomendar_playlist(sentimento):
    categoria = escolher_categoria(sentimento)

    try:
        results = sp.search(q=categoria, type="playlist", limit=5)

        if results and "playlists" in results and "items" in results["playlists"]:
            playlists = results["playlists"]["items"]

            if playlists:
                print(f"\n🎶 Playlists recomendadas para o humor: {sentimento}\n")
                for idx, playlist in enumerate(playlists):
                    if playlist:
                        nome = playlist.get("name", "Nome desconhecido")
                        playlist_id = playlist.get("id")

                        if playlist_id:
                            print(f"{idx + 1}. {nome} - {playlist_id}")
                        else:
                            print(f"{idx + 1}. [Playlist sem ID encontrado]")
            else:
                print("Nenhuma playlist encontrada.")
        else:
            print("A resposta da API não contém playlists.")

    except Exception as e:
        print(f"Erro ao buscar playlists: {e}")

# Teste com diferentes sentimentos
recomendar_playlist("Positivo 😀")
recomendar_playlist("Negativo 😢")
recomendar_playlist("Neutro 😐")