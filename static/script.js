function getSentimentoIcon(sentimento) {
    const icones = {
        "Positivo 😀": "😃",
        "Negativo 😢": "😢",
        "Neutro 😐": "😐",
        "Raiva 😡": "😡",
        "Motivação 💪": "💪",
        "Nostalgia 🕰️": "🕰️",
        "Indefinido 🤔": "❓"
    };
    return icones[sentimento] || "❓";
}

async function buscarPlaylist() {
    let texto = document.getElementById("texto").value;
    let playlistContainer = document.getElementById("playlist-container");
    let feedbackContainer = document.getElementById("feedback-container");
    let mensagemErro = document.getElementById("mensagem-erro");
    let loading = document.getElementById("loading");

    if (texto.trim() === "") {
        mensagemErro.innerText = "Por favor, escreva algo!";
        return;
    }

    mensagemErro.innerText = "";
    playlistContainer.style.display = "none";
    feedbackContainer.style.display = "none";
    loading.style.display = "block";

    let response = await fetch("/recomendar_playlist/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: texto })
    });

    let data = await response.json();
    loading.style.display = "none";

    if (data.erro) {
        mensagemErro.innerText = data.erro;
    } else {
        let playlist = data.playlist_recomendada;
        let sentimento = data.sentimento;
        let sentimentoIcon = getSentimentoIcon(sentimento);

        document.getElementById("playlist-sentimento").innerHTML = `${sentimentoIcon} ${sentimento}`;
        document.getElementById("playlist-nome").innerText = playlist.nome;
        document.getElementById("playlist-image").src = playlist.image;
        document.getElementById("playlist-link").href = `https://open.spotify.com/playlist/${playlist.id}`;
        playlistContainer.style.display = "block";
        feedbackContainer.style.display = "block"; 

        carregarHistorico();
    }
}

async function carregarHistorico() {
    let response = await fetch("/historico/");
    let data = await response.json();

    let tabela = document.getElementById("historico-tabela");
    tabela.innerHTML = "";

    if (data.length === 0) {
        tabela.innerHTML = "<tr><td colspan='4'>Nenhum histórico encontrado.</td></tr>";
        return;
    }

    data.forEach(item => {
        let sentimentoIcon = getSentimentoIcon(item.sentimento);
        let row = `<tr>
            <td>${item.texto_digitado}</td>
            <td>${sentimentoIcon} ${item.sentimento}</td>
            <td>${item.playlist_nome}</td>
            <td><a href="${item.link}" target="_blank" class="btn btn-sm btn-success">🎵 Ouvir</a></td>
        </tr>`;
        tabela.innerHTML += row;
    });
}

async function carregarEstatisticas() {
    let response = await fetch("/estatisticas/");
    let data = await response.json();

    let ctx = document.getElementById("grafico-estatisticas").getContext("2d");

    // Se já existe um gráfico, destruí-lo antes de criar um novo
    if (window.graficoEstatisticas) {
        window.graficoEstatisticas.destroy();
    }

    window.graficoEstatisticas = new Chart(ctx, {
        type: "doughnut",  // Gráfico de pizza atualizado 🍩
        data: {
            labels: ["Positivo 😀", "Negativo 😢", "Neutro 😐", "Raiva 😡", "Motivação 💪", "Nostalgia 🕰️"],
            datasets: [{
                label: "Quantidade de buscas",
                data: [
                    data["Positivo 😀"], 
                    data["Negativo 😢"], 
                    data["Neutro 😐"], 
                    data["Raiva 😡"],
                    data["Motivação 💪"],
                    data["Nostalgia 🕰️"]
                ],
                backgroundColor: ["#28a745", "#dc3545", "#ffc107", "#6c757d", "#007bff", "#ff69b4"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}

async function enviarFeedback(confirmado) {
    let sentimentoAtual = document.getElementById("playlist-sentimento").innerText;
    let sentimentoCorrigido = null;

    if (!confirmado) {
        sentimentoCorrigido = prompt("Qual seria o sentimento correto?");
        if (!sentimentoCorrigido) return; // Se o usuário cancelar, não faz nada
    }

    let response = await fetch("/feedback/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            sentimento: sentimentoAtual, 
            confirmado: confirmado, 
            correcao: sentimentoCorrigido 
        })
    });

    let data = await response.json();
    alert(data.mensagem);
}

async function carregarEstatisticasFeedback() {
    let response = await fetch("/estatisticas_feedback/");
    let data = await response.json();

    let ctx = document.getElementById("grafico-feedback").getContext("2d");

    if (window.graficoFeedback) {
        window.graficoFeedback.destroy();
    }

    window.graficoFeedback = new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["Confirmados ✅", "Corrigidos ❌"],
            datasets: [{
                data: [data["Confirmados"], data["Corrigidos"]],
                backgroundColor: ["#28a745", "#dc3545"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", function() {
    const darkModeToggle = document.getElementById("darkModeToggle");
    const body = document.body;

    // Verificar se já há uma preferência salva
    if (localStorage.getItem("darkMode") === "enabled") {
        body.classList.add("dark-mode");
    }

    // Alternar Dark Mode
    darkModeToggle.addEventListener("click", function() {
        body.classList.toggle("dark-mode");
        if (body.classList.contains("dark-mode")) {
            localStorage.setItem("darkMode", "enabled");
        } else {
            localStorage.setItem("darkMode", "disabled");
        }
    });
});

// Atualiza os gráficos ao carregar a página
window.onload = function () {
    carregarHistorico();
    setTimeout(carregarEstatisticas, 500);
    setTimeout(carregarEstatisticasFeedback, 800);
};
