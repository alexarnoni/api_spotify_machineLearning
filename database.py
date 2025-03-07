from tortoise import fields, models
from tortoise.contrib.fastapi import register_tortoise
from dotenv import load_dotenv
import os

# Carregar variáveis do .env
load_dotenv()

class HistoricoBusca(models.Model):
    id = fields.IntField(pk=True)
    texto_digitado = fields.TextField()
    sentimento = fields.CharField(max_length=255)
    playlist_nome = fields.CharField(max_length=255)
    playlist_id = fields.CharField(max_length=255)

    class Meta:
        table = "historico_buscas"

class Feedback(models.Model):
    id = fields.IntField(pk=True)
    sentimento_detectado = fields.CharField(max_length=255)
    sentimento_corrigido = fields.CharField(max_length=255, null=True)
    confirmado = fields.BooleanField()

    class Meta:
        table = "feedbacks"

def init_db(app):
    register_tortoise(
        app,
        db_url=os.getenv("DATABASE_URL"),
        modules={"models": ["database"]},
        generate_schemas=True,  # 🔥 Garante que a tabela seja criada automaticamente
        add_exception_handlers=True,
    )
