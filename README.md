# 🎬 Gerador de prompts — Copa 2026

Automação que envia todo dia às **07:00 (Brasília)** um e-mail com prompts de vídeo
prontos pra colar no **Google Flow (Veo 3)**, no formato do canal
[@posteimasfoieu](https://www.youtube.com/@posteimasfoieu/shorts):

- entrevista flash pós-jogo hiper-realista (~8s)
- jogador/técnico/torcedor responde com **seriedade total** uma piada de meme
- manchete preta clickbait + legenda amarela + 3 emojis 😂 (adicionados na edição)

## O que o e-mail traz

| Seção | Conteúdo |
|---|---|
| 🏁 Pós-jogo | 3 prompts por jogo de **ontem**, com o placar real (vencedor zoando, perdedor com desculpa absurda, técnico na coletiva) |
| 📅 Pré-jogo | 2 prompts por jogo de **hoje** (jogador subestimando o adversário, torcedor confiante) |
| 🔥 Viral | prompt sob medida quando você informa o lance viral do dia |

Os placares vêm da API pública da ESPN; se ela falhar, usa a tabela local
(`dados/jogos_seed.json`).

## Configurar (uma vez só, ~3 minutos)

1. Crie uma **senha de app** do Gmail: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   (precisa ter verificação em 2 etapas ativa).
2. No repositório: **Settings → Secrets and variables → Actions → New repository secret**:
   - `GMAIL_USUARIO` → `niusouza@gmail.com`
   - `GMAIL_SENHA_APP` → a senha de app gerada (16 letras)
3. Pronto. O e-mail chega todo dia às 7h durante a Copa (11/06 a 19/07).

## Lance viral no meio do dia?

**Actions → Prompts diários da Copa → Run workflow** → preencha o campo
`momento_viral` (ex: *"árbitro brasileiro deu 3 vermelhos na estreia e virou
meme pelo inglês"*) → chega um e-mail extra com o prompt do viral.

## Rodar local

```bash
python3 gerar_prompts.py                                # jogos de ontem + hoje
MOMENTO_VIRAL="descrição do lance" python3 gerar_prompts.py
```

## Ajustar o humor

- `dados/grupos.json` — banco de memes por seleção (1 a 3 piadas por país) e cores do uniforme
- `gerar_prompts.py` — desculpas absurdas (`DESCULPAS`), perguntas e os moldes de cena
