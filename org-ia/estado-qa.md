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

**(nenhuma ainda)**

---

## Bugs ativos

**(nenhum ainda)**

---

## Histórico de execuções

| Data | Resultado | Empresa QA usada | Observação |
|---|---|---|---|
| — | — | — | — |

---

## Hipóteses em aberto

**(nenhuma ainda)**
