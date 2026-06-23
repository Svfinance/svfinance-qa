# org-ia/estado-qa.md — Memória Operacional do QA

Este arquivo é a fonte de verdade entre sessões de teste. Sempre que um teste
falhar, o estado deve ser registrado aqui de forma estruturada — seja por um
script automatizado, seja manualmente por Guilherme ou pelo agente ativo.

Ao iniciar qualquer sessão neste repositório, leia este arquivo primeiro.
Ele responde: o que está pendente, o que já foi tentado, e o que falta investigar.

---

## Formato de entrada de bug

```
## BUG-00X — <módulo>
- Data/hora:
- Cenário testado:
- Resultado esperado:
- Resultado obtido:
- Evidência: reports/<data>/<arquivo>
- Status: NÃO INVESTIGADO | EM INVESTIGAÇÃO | CORRIGIDO | IGNORADO (falso positivo)
- Hipótese de causa (se houver):
```

**Status possíveis:**
- `NÃO INVESTIGADO` — falha detectada, ainda não analisada
- `EM INVESTIGAÇÃO` — sendo investigada (registrar hipótese abaixo)
- `CORRIGIDO` — fix aplicado no svfinance-api (registrar commit)
- `IGNORADO (falso positivo)` — falha de ambiente ou dado de teste, não é bug real

---

## Última execução

**Data:** 2026-06-23  
**Resultado:** 80 falha(s) total — 80 falha(s) em teste(s) — 2 BUG(s) novo(s), 78 duplicata(s)  
**Arquivo:** reports/2026-06-23/falhas.jsonl


## Histórico de execuções

| Data | Resultado | Empresa QA usada | Observação |
|---|---|---|---|
| 2026-06-23 | 80 falha(s) total — 80 falha(s) em teste(s) — 2 BUG(s) novo(s), 78 duplicata(s) | — | — |
| 2026-06-22 | 78 falha(s) total — 78 falha(s) em teste(s) — 23 BUG(s) novo(s), 55 duplicata(s) | — | — |
| 2026-06-20 | 9✅ 9❌ 7⏭️ | seed QA existente | Primeira execução real contra produção |

---

## Hipóteses em aberto

1. **BUG-002**: o form de criação de cliente fecha silenciosamente (sem criar) quando chamado no segundo teste da mesma suíte — investigar se há validação de duplicidade por nome ou race condition com React state
2. **BUG-003**: `fill()` em input controlado pelo React com valor pré-existente não dispara onChange — testar com `click({clickCount:3}) + fill()` ou `pressSequentially()`
3. **UX-001/002**: confirmar com Guilherme se ausência de auto-refresh nas listas é design intencional ou bug a corrigir no frontend
