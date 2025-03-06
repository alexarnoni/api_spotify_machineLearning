function getSentimentoIcon(sentimento) {
    const icones = {
        "Positivo 😀": "😃",
        "Negativo 😢": "😢",
        "Neutro 😐": "😐",
        "Raiva 😡": "😡",
        "Indefinido 🤔": "❓"
    };
    return icones[sentimento] || "❓";
}

async function buscarPlaylist() {
    let texto = document.getElementById("texto").value;
    let playlistContainer = document.getElementById("playlist-container");
    let mensagemErro = document.getElementById("mensagem-erro");
    let loading = document.getElementById("loading");

    if (texto.trim() === "") {
        mensagemErro.innerText = "Por favor, escreva algo!";
        return;
    }

    mensagemErro.innerText = "";
    playlistContainer.style.display = "none";
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
        
        // Atualizar histórico após uma nova recomendação
        carregarHistorico();
    }
}

async function carregarHistorico() {
    let response = await fetch("/historico/");
    let data = await response.json();

    let tabela = document.getElementById("historico-tabela");
    tabela.innerHTML = "";  // Limpa a tabela antes de adicionar novas entradas

    if (data.length === 0) {
        tabela.innerHTML = "<tr><td colspan='4'>Nenhum histórico encontrado.</td></tr>";
        return;
    }

    data.forEach(item => {
        let row = `<tr>
            <td>${item.texto_digitado}</td>
            <td>${item.sentimento}</td>
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
        type: "pie",  // Alterado para gráfico de pizza 🍕
        data: {
            labels: ["Positivo 😀", "Negativo 😢", "Neutro 😐", "Raiva 😡"],
            datasets: [{
                label: "Quantidade de buscas",
                data: [data["Positivo 😀"], data["Negativo 😢"], data["Neutro 😐"], data["Raiva 😡"]],
                backgroundColor: ["#28a745", "#dc3545", "#ffc107", "#6c757d"]
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

window.onload = function () {
    carregarHistorico(); // Carregar histórico automaticamente ao abrir a página
    setTimeout(carregarEstatisticas, 500);  // Pequeno atraso para evitar conflitos no carregamento
};

