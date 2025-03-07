from transformers import pipeline

# Criando pipeline de análise de sentimentos para português
sentiment_analysis = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

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

# Testando com frases em português
testes = [
    "Hoje é um dia maravilhoso! Estou muito feliz!",
    "Que dia terrível... nada dá certo.",
    "Estou cansado e sem energia, mas ainda tenho esperança.",
    "A música é maravilhosa, me sinto animado!",
    "Isso foi péssimo, nunca mais quero passar por isso.",
    "to me sentindo bem mais ou menos hoje",
    "não sei"
]

for frase in testes:
    print(f"Texto: {frase} → {analisar_sentimento_bert(frase)}")
