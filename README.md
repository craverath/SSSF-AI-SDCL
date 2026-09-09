# Super Simple Software Factory

> Workflows repetíveis de **agentes + código**, empacotados como uma skill e estampados em qualquer repositório.

<p align="center">
  <img src="images/00_swimlane_waterfall.svg" alt="Uma execução em raias: engineer, code, planner, builder e reviewer dispostos em um eixo de tempo, cada bloco com sua duração, uma fase ainda rodando e a próxima na fila" width="850">
</p>

Um script Python determinístico (o **ADW** — AI Developer Workflow) é dono da sequência, das repetições e do critério de aceite. Os agentes de código trabalham dentro de **fases** delimitadas. Envelopes JSON tipados carregam o contexto entre elas. Todo evento cai no SQLite enquanto ainda está acontecendo, então você acompanha a execução ao vivo em vez de ler um transcript depois.

**O agente propõe, o código decide.**

📺 Visão geral no YouTube: **[Super Simple Software Factory](https://youtu.be/haUfb1ievTE)**

## TL;DR

Quatro comandos, da raiz do repositório em que a fábrica vai operar:

```bash
git clone --depth 1 https://github.com/craverath/SSSF-AI-SDCL.git sssf
uv run sssf/install.py --integration kiro   # ou claude | codex | none
just demo                                   # smoke test read-only
just obs                                    # UI de traces em :4601
```

As seções abaixo explicam o que cada um faz e o que muda por host.

---

## 1. Clone

Clone a fábrica **dentro do repositório em que ela vai operar**, com o nome `sssf/`:

```bash
cd ~/code/seu-projeto
git clone --depth 1 https://github.com/craverath/SSSF-AI-SDCL.git sssf
```

O instalador resolve os templates a partir do próprio arquivo, então precisa de um clone real em disco — não existe `curl | sh`. Manter o clone dentro do repo faz a fábrica viajar com o projeto, e atualizar é `git -C sssf pull`. O `install.py` adiciona `sssf/` ao seu `.gitignore`.

## 2. Pré-requisitos

| O quê | Para quê |
|---|---|
| [`uv`](https://docs.astral.sh/uv/) | roda os ADWs e o instalador |
| `sqlite3` | lê o banco de traces (`just sessions`, `just phases`) |
| CLI de cada agente do roster, **já autenticado** | `pi`, `claude`, `codex`, `kiro-cli` ou `agy` |
| [`bun`](https://bun.sh) | só a UI de traces (`just obs`) |
| [`just`](https://just.systems) | opcional — todas as receitas são uma linha de shell |

Checagem em uma linha:

```bash
for cli in uv sqlite3 bun just pi claude codex kiro-cli agy; do
  command -v "$cli" >/dev/null && echo "ok   $cli" || echo "falta $cli"
done
```

Um roster só é real se o binário atrás dele existe e está logado: cada adapter chama um CLI.

## 3. Instale

Rode a partir da **raiz do repositório de destino**, escolhendo o host de onde *você* vai operar a fábrica:

```bash
uv run sssf/install.py --integration kiro
```

A flag `--integration` define **onde as skills são instaladas e como o host as expõe**. Ela não muda o `coding_agent` de nenhum agente do workflow.

| Flag | Skills instaladas em | Como invocar |
|---|---|---|
| `--integration claude` | `.claude/skills/` | `/sssf`, `/sssf-grill-me`, `/sssf-pick-models` |
| `--integration codex` | `.agents/skills/` | `$sssf`, `$sssf-grill-me`, `$sssf-pick-models` |
| `--integration kiro` | `.kiro/skills/` | `/sssf`, `/sssf-grill-me`, `/sssf-pick-models` |
| `--integration none` | — | só a fábrica, sem integração de host |

Omitir a flag equivale a `claude`. No Kiro CLI nada precisa ser configurado: o agente padrão já carrega `skill://.kiro/skills/*/SKILL.md`.

Reinstalar é seguro — arquivos existentes são preservados e o que foi ignorado é reportado. `--force` sobrescreve **tudo**, incluindo seu `sssf.config.yaml` e seus prompts; comite antes.

Duas coisas antes da primeira execução que escreve código:

1. Comite a fábrica estampada (`git add -A && git commit -m "stamp sssf"`). A fase de commit é `git add -A` e levaria a instalação inteira para o commit do builder.
2. Ligue seus comandos reais em `adws/adw_modules/quality.py` — os que vêm de fábrica são placeholders que retornam 0.

## 4. Mande o primeiro prompt

Antes de qualquer coisa, o smoke test — duas execuções baratas e read-only que provam o caminho inteiro:

```bash
just demo
just sessions
```

Verde significa: config validada, harness executado, envelope parseado e eventos gravados em `adws/adw_data/sssf.db`. Conserte aqui antes de compor algo maior.

Depois, o fluxo completo aceita um prompt inline ou o caminho de uma especificação:

```bash
just sssf "adicione um endpoint /health"
just sssf specs/2026-09-09-health-endpoint.md
```

Sem `just`, a forma crua é a mesma para qualquer workflow:

```bash
uv run adws/adw_simple_sdlc.py "adicione um endpoint /health" [--adw-id a1b2c3d4]
```

`--adw-id` é opcional. Sem ele, um id novo é criado e impresso; com ele, a execução entra na sessão existente e cada agente **retoma seu contexto** em vez de começar do zero. É assim que se encadeia workflows.

## 5. Ligue o obs

Em um segundo terminal, e deixe aberto:

```bash
just obs
```

UI em `http://localhost:4601`, API em `:4600`. Na primeira execução instala as dependências do visualizador (precisa de `bun`). A UI é somente leitura e faz poll do SQLite — o banco está em WAL, então ler nunca bloqueia uma execução em andamento.

---

## As três skills

O produto é a skill. São três, instaladas lado a lado pelo `--integration`.

**`sssf`** — o orquestrador da fábrica. Roteia seu pedido para um de nove cookbooks carregados sob demanda: instalar, criar um ADW, alterar uma cadeia, criar ou ajustar o roster de agentes, estender `adw_modules`, rodar e monitorar. Ele opera e observa a fábrica; não faz o trabalho dos agentes.

**`sssf-grill-me`** — entrevista antes de codificar. Inspeciona o código relevante, faz as perguntas que só você pode responder (decisões de produto, não fatos que o código já responde) e escreve uma especificação aprovada em `specs/`. Não altera a aplicação e não dispara a fábrica — você decide quando enviar o arquivo.

**`sssf-pick-models`** — define qual harness e qual modelo roda cada agente. Carrega os catálogos de modelos dos cinco harnesses, mostra o que cada papel está comprando e escreve o resultado em `sssf.config.yaml`, incluindo as chaves que uma troca de harness obriga (o `tools: null` que `codex`, `kiro_cli` e `antigravity` exigem, e que uma edição manual normalmente erra). Rode logo depois de instalar: o roster inicial nomeia os modelos que eram bons na semana em que foi escrito.

Nos três casos, os prompts que chegam ao seu repositório são seus. Edite em `adws/adw_data/prompt_engineering/{agent}/`, nunca de volta dentro da skill.

---

## Onde está o resto

Os documentos abaixo com caminho `docs/` ou `.../skills/` estão em inglês — são o texto original do upstream, preservado sem tradução.

| Assunto | Onde |
|---|---|
| Documentação completa: por que a fábrica existe, fases, envelopes, gates, trace e os doze workflows iniciais | [`docs/README-full.md`](docs/README-full.md) |
| Troubleshooting: modos de falha conhecidos e o que fazer em cada um | [`docs/README-full.md#where-it-can-still-fail`](docs/README-full.md#where-it-can-still-fail) |
| Regras duras e roteamento de pedidos | `.{claude,agents,kiro}/skills/sssf/SKILL.md` |
| Cookbooks (instalar, criar/alterar ADW, config, monitorar) | `.../skills/sssf/cookbooks/` |
| Especificações profundas: config, handoff, observabilidade | `.../skills/sssf/references/` |
| Roster de agentes: modelo, thinking, tools, `writes` | `adws/adw_sssf_config/sssf.config.yaml` |
| Seus prompts | `adws/adw_data/prompt_engineering/{agent}/` |
| Seus comandos de lint, typecheck, build e teste | `adws/adw_modules/quality.py` |
| Sua definição de "pronto" | `adws/adw_modules/gates.py` |
| Receitas prontas de execução e observação | `justfile` |

Um repositório com a fábrica já estampada, um app demo que ela planejou, construiu, testou, revisou e documentou, e os traces reais dessas execuções: [branch `example`](../../tree/example).

---

## Licença

MIT, ver [`LICENSE`](LICENSE).

Baseado no trabalho de [IndyDevDan](https://www.youtube.com/@indydevdan) — [Tactical Agentic Coding](https://agenticengineer.com/tactical-agentic-coding?y=sssf).
