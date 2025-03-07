let apiUrl = "https://api-spotify-ml.onrender.com"; // URL do backend hospedado no Render

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

    try {
        let response = await fetch(`${apiUrl}/recomendar_playlist/`, {
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
    } catch (error) {
        mensagemErro.innerText = "Erro ao buscar playlist. Tente novamente mais tarde.";
        console.error("Erro ao buscar playlist:", error);
    }
}

async function carregarHistorico() {
    try {
        let response = await fetch(`${apiUrl}/historico/`);
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
    } catch (error) {
        console.error("Erro ao carregar histórico:", error);
    }
}

async function carregarEstatisticas() {
    let response = await fetch(`${apiUrl}/estatisticas/`);
    let data = await response.json();
    
    let ctx = document.getElementById("grafico-estatisticas").getContext("2d");
    
    if (window.graficoEstatisticas) {
        window.graficoEstatisticas.destroy();
    }

    window.graficoEstatisticas = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Positivo 😀", "Negativo 😢", "Neutro 😐", "Raiva 😡", "Motivação 💪", "Nostalgia 🕰️"],
            datasets: [{
                data: [
                    data["Positivo 😀"] || 0,
                    data["Negativo 😢"] || 0,
                    data["Neutro 😐"] || 0,
                    data["Raiva 😡"] || 0,
                    data["Motivação 💪"] || 0,
                    data["Nostalgia 🕰️"] || 0
                ],
                backgroundColor: ["#28a745", "#dc3545", "#ffc107", "#6c757d", "#007bff", "#ff69b4"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom" }
            }
        }
    });
}

async function enviarFeedback(confirmado) {
    let sentimentoAtual = document.getElementById("playlist-sentimento").innerText;
    let sentimentoCorrigido = null;

    if (!confirmado) {
        sentimentoCorrigido = prompt("Qual seria o sentimento correto?");
        if (!sentimentoCorrigido) return;
    }

    try {
        let response = await fetch(`${apiUrl}/feedback/`, {
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
    } catch (error) {
        console.error("Erro ao enviar feedback:", error);
    }
}

// 🚀 Configurar Dark Mode corretamente
document.addEventListener("DOMContentLoaded", function () {
    const darkModeToggle = document.getElementById("darkModeToggle");
    const body = document.body;

    if (localStorage.getItem("darkMode") === "enabled") {
        body.classList.add("dark-mode");
    }

    darkModeToggle.addEventListener("click", function () {
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