#!/usr/bin/env python3
"""Gerador diário de prompts de vídeo (Veo 3 / Google Flow) para a Copa 2026.

Formato do canal @posteimasfoieu:
  - clipe de ~8s: entrevista flash pós-jogo hiper-realista
  - jogador/técnico responde com seriedade total uma piada de meme
  - manchete preta clickbait + legendas amarelas + emojis (adicionados na edição)

Uso:
  python3 gerar_prompts.py                  # jogos de ontem (pós) + hoje (pré)
  MOMENTO_VIRAL="descrição" python3 ...     # adiciona bloco sobre o viral do dia

Saída: saida/email.txt (corpo do e-mail) e saida/assunto.txt
"""

import json
import os
import random
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).parent
BRASILIA = timezone(timedelta(hours=-3))
ESPN_URL = ("https://site.api.espn.com/apis/site/v2/sports/soccer/"
            "fifa.world/scoreboard?dates={data}")

# ---------------------------------------------------------------- dados

GRUPOS = json.loads((RAIZ / "dados" / "grupos.json").read_text(encoding="utf-8"))
SEED = json.loads((RAIZ / "dados" / "jogos_seed.json").read_text(encoding="utf-8"))

TIMES = {}
for grupo, selecoes in GRUPOS.items():
    for t in selecoes:
        t["grupo"] = grupo
        TIMES[t["pt"]] = t
        TIMES[t["en"]] = t

GENERICO = {"pt": None, "cores": "uniforme da seleção", "memes": ["a zebra que ninguém esperava"]}

DESCULPAS = [
    "A culpa foi da chuva. Não choveu, mas podia ter chovido.",
    "O wifi do hotel caiu e ninguém assistiu os vídeos do adversário.",
    "A gente achou que era amistoso. Ninguém avisou que valia.",
    "O GPS do ônibus levou a gente pro estádio errado, chegamos sem aquecer.",
    "A comida daqui não tem tempero. Como é que joga sem tempero?",
    "O fuso horário. Meu corpo ainda tá no horário do meu país, e lá agora é hora de dormir.",
    "O gramado tava muito verde. A gente se distraiu.",
    "Ninguém falou que o juiz era brasileiro. A gente teria se comportado.",
]

PERGUNTAS_DERROTA = ["O que aconteceu?", "Como explicar essa derrota?", "O que deu errado hoje?"]
PERGUNTAS_VITORIA = ["Qual foi o segredo da vitória?", "O que achou do jogo?", "Como o time se preparou?"]
PERGUNTAS_PRE = ["Como o time está pra estreia?", "O que esperar do jogo de hoje?", "Estudaram o adversário?"]


def de(time):
    """Contração 'de' + artigo do país: do Brasil, da Suíça, dos EUA, de Portugal."""
    return {"o": "do", "a": "da", "os": "dos", "": "de"}[time.get("art", "o")]


def com_artigo(time, caixa_alta=True):
    """'O BRASIL', 'A SUÍÇA', 'OS ESTADOS UNIDOS', 'PORTUGAL'."""
    art = time.get("art", "o")
    nome = f"{art} {time['pt']}".strip()
    return nome.upper() if caixa_alta else nome


def cena(time, fala_reporter, fala_jogador, extra=""):
    """Monta o prompt no formato que o canal usa, pronto pro Flow.

    Descrição da cena em inglês (o Flow aceita melhor e bloqueia menos),
    falas sempre em português-BR. Sem nomes reais, sem marcas.
    """
    cores = time.get("cores", "his national team kit")
    return (
        "Hyper-realistic TV broadcast footage of a post-match flash interview "
        "at a major international football tournament. A sweaty football "
        f"player wearing a {cores}, standing in front of a reporter's "
        "microphone, blurred cheering crowd in a packed stadium under night "
        "floodlights in the background. "
        f'The reporter asks in Brazilian Portuguese: "{fala_reporter}" '
        "The player answers completely deadpan, without smiling, in Brazilian "
        f'Portuguese: "{fala_jogador}" '
        f"{extra}"
        "Stadium crowd ambience. Sports broadcast camera, medium shot, slight "
        "handheld movement. IMPORTANT: all spoken dialogue must be in "
        "Brazilian Portuguese with natural native pronunciation."
    )


def bloco(manchete, prompt):
    return f"📌 MANCHETE (texto preto no topo): {manchete}\n\n🎬 PROMPT (colar no Flow):\n{prompt}\n"


def prompts_pos_jogo(vencedor, perdedor, placar, rng):
    """3 prompts para um jogo já encerrado."""
    blocos = []

    meme_perd = rng.choice(perdedor["memes"])
    blocos.append(bloco(
        f"JOGADOR {de(vencedor).upper()} {vencedor['pt'].upper()} NÃO PERDOOU KKK",
        cena(vencedor, rng.choice(PERGUNTAS_VITORIA),
             f"Olha, a gente respeita muito eles. Mas {meme_perd}. Aí fica fácil.")))

    blocos.append(bloco(
        f"JOGADOR EXPLICA DERROTA {de(perdedor).upper()} {perdedor['pt'].upper()}",
        cena(perdedor, rng.choice(PERGUNTAS_DERROTA),
             rng.choice(DESCULPAS),
             "The player looks visibly shaken while the rival crowd celebrates "
             "behind him. ")))

    blocos.append(bloco(
        f"TÉCNICO REVELA SEGREDO ({placar}) 😳",
        "Hyper-realistic press conference at a major international football "
        "tournament. A football head coach in a suit, sitting behind a "
        "microphone with a generic sponsor backdrop, camera flashes going off. "
        'A journalist asks in Brazilian Portuguese: "Qual foi a chave do jogo?" '
        "The coach answers deadpan in Brazilian Portuguese: "
        f'"Simples. Todo mundo sabe que {meme_perd}. Nós só lembramos eles '
        'disso no vestiário." Muffled laughter from the journalists. Press '
        "room audio. IMPORTANT: all spoken dialogue must be in Brazilian "
        "Portuguese with natural native pronunciation."))
    return blocos


def prompts_pre_jogo(casa, fora, rng):
    """2 prompts para jogo que ainda vai acontecer."""
    blocos = []
    alvo, falante = (casa, fora) if rng.random() < 0.5 else (fora, casa)
    meme_alvo = rng.choice(alvo["memes"])

    blocos.append(bloco(
        f"JOGADOR SUBESTIMOU {com_artigo(alvo)} KKK",
        cena(falante, rng.choice(PERGUNTAS_PRE),
             f"Estudar o quê? {meme_alvo.capitalize()}. Eu vim mais pelo turismo, "
             "se eu for sincero.",
             "It is a pre-match mixed zone, the player wears a training "
             "tracksuit. ")))

    blocos.append(bloco(
        f"TORCEDOR JÁ GARANTIU O RESULTADO 😂",
        "Hyper-realistic street interview on matchday outside a packed "
        "football stadium during a major international tournament. A "
        f"passionate football fan wearing a {falante.get('cores', 'team jersey')} "
        "with his face painted, holding nothing back. The reporter asks in "
        'Brazilian Portuguese: "Qual o placar de hoje?" The fan answers with '
        "absolute confidence in Brazilian Portuguese: "
        f'"Já ganhou. {meme_alvo.capitalize()}, anota aí." Then he walks away '
        "without waiting for the next question. Crowd audio. IMPORTANT: all "
        "spoken dialogue must be in Brazilian Portuguese with natural native "
        "pronunciation."))
    return blocos


def prompt_viral(descricao):
    return bloco(
        "O VIRAL DO DIA 🔥 (adapte a manchete)",
        "Hyper-realistic TV broadcast footage of a post-match flash interview "
        "at a major international football tournament, packed stadium in the "
        "background. Build the scene around the viral moment described below "
        "— the interviewee treats the absurd situation with complete "
        "seriousness, as if it were the most normal thing in the world. "
        "Do NOT mention real names or brands; describe people generically "
        "(e.g. 'a Brazilian football referee'):\n"
        f"VIRAL MOMENT: {descricao}\n"
        "Stadium ambience, sports broadcast camera, medium shot. IMPORTANT: "
        "all spoken dialogue must be in Brazilian Portuguese with natural "
        "native pronunciation.")


# ---------------------------------------------------------------- fixtures

def busca_espn(dia):
    """Jogos do dia via API pública da ESPN. Retorna lista de dicts."""
    url = ESPN_URL.format(data=dia.strftime("%Y%m%d"))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        dados = json.load(resp)
    jogos = []
    for ev in dados.get("events", []):
        comp = ev["competitions"][0]
        lados = {c["homeAway"]: c for c in comp["competitors"]}
        casa, fora = lados["home"], lados["away"]
        jogos.append({
            "casa": casa["team"]["displayName"],
            "fora": fora["team"]["displayName"],
            "placar_casa": int(casa.get("score") or 0),
            "placar_fora": int(fora.get("score") or 0),
            "encerrado": comp.get("status", ev.get("status", {})).get("type", {}).get("completed", False),
        })
    return jogos


def busca_seed(dia):
    alvo = dia.strftime("%Y-%m-%d")
    return [{"casa": j["casa"], "fora": j["fora"], "placar_casa": None,
             "placar_fora": None, "encerrado": None}
            for j in SEED["jogos"] if j["data"] == alvo]


def jogos_do_dia(dia):
    try:
        jogos = busca_espn(dia)
        if jogos:
            return jogos, "espn"
    except Exception:
        pass
    return busca_seed(dia), "seed"


def time_info(nome):
    if nome in TIMES:
        return TIMES[nome]
    g = dict(GENERICO)
    g["pt"] = nome
    return g


# ---------------------------------------------------------------- e-mail

def main():
    hoje = datetime.now(BRASILIA).date()
    ontem = hoje - timedelta(days=1)
    rng = random.Random(str(hoje))
    linhas = []

    linhas.append(f"🎬 PROMPTS DO DIA — {hoje.strftime('%d/%m/%Y')}")
    linhas.append("")
    linhas.append("Lembrete do formato: gerar no Flow (Veo 3, 9:16 se disponível, senão "
                  "cortar na edição) → adicionar manchete preta em caixa alta no topo, "
                  "legenda amarela com o diálogo e 3 emojis 😂 embaixo (CapCut).")
    linhas.append("Os prompts vêm em inglês (o Flow bloqueia menos), mas as falas saem "
                  "em português-BR. Sem nomes reais nem marcas, pra não violar diretrizes.")
    linhas.append("=" * 60)

    de_ontem, fonte_ontem = jogos_do_dia(ontem)
    if de_ontem:
        linhas.append(f"\n🏁 PÓS-JOGO — jogos de ontem ({ontem.strftime('%d/%m')})\n")
        for j in de_ontem:
            casa, fora = time_info(j["casa"]), time_info(j["fora"])
            if j["encerrado"] is False:
                continue
            if j["placar_casa"] is None or j["placar_casa"] == j["placar_fora"]:
                # sem placar (seed) ou empate: zoa os dois lados, escolhe um
                vencedor, perdedor = rng.sample([casa, fora], 2)
                placar = "empate" if j["placar_casa"] is not None else "resultado: confira"
            elif j["placar_casa"] > j["placar_fora"]:
                vencedor, perdedor = casa, fora
                placar = f"{j['placar_casa']}x{j['placar_fora']}"
            else:
                vencedor, perdedor = fora, casa
                placar = f"{j['placar_fora']}x{j['placar_casa']}"
            linhas.append(f"⚽ {casa['pt']} x {fora['pt']} ({placar})\n")
            linhas.extend(prompts_pos_jogo(vencedor, perdedor, placar, rng))
            linhas.append("-" * 60)

    de_hoje, fonte_hoje = jogos_do_dia(hoje)
    if de_hoje:
        linhas.append(f"\n📅 PRÉ-JOGO — jogos de hoje ({hoje.strftime('%d/%m')})\n")
        for j in de_hoje:
            casa, fora = time_info(j["casa"]), time_info(j["fora"])
            linhas.append(f"⚽ {casa['pt']} x {fora['pt']}\n")
            linhas.extend(prompts_pre_jogo(casa, fora, rng))
            linhas.append("-" * 60)

    if not de_ontem and not de_hoje:
        linhas.append("\nSem jogos ontem nem hoje. Dia de descanso (ou de repostar o que bombou).")

    viral = os.environ.get("MOMENTO_VIRAL", "").strip()
    if viral:
        linhas.append("\n🔥 MOMENTO VIRAL INFORMADO\n")
        linhas.append(prompt_viral(viral))

    linhas.append("")
    linhas.append(f"Fontes de jogos: ontem={fonte_ontem if de_ontem else '-'}, "
                  f"hoje={fonte_hoje if de_hoje else '-'} "
                  "(espn = placar real; seed = tabela local, confira o placar)")
    linhas.append("Pra gerar prompt de um lance viral: rode o workflow manualmente em "
                  "Actions → Prompts diários da Copa → Run workflow, preenchendo o campo "
                  "'momento_viral'.")

    corpo = "\n".join(linhas)
    saida = RAIZ / "saida"
    saida.mkdir(exist_ok=True)
    (saida / "email.txt").write_text(corpo, encoding="utf-8")
    (saida / "assunto.txt").write_text(
        f"🎬 Prompts Copa 2026 — {hoje.strftime('%d/%m')}", encoding="utf-8")
    print(corpo)


if __name__ == "__main__":
    main()
