# 🐉 NECROZMAv2

> *"288 estratégias entram. 13 lendários emergem. O resto vira história."*

## 🔥 O que é?

NECROZMAv2 é um sistema de trading automatizado que:

- ⚡ Testa **288 estratégias** em minutos
- 🏆 Seleciona os **13 melhores** (Lendários)
- 🔄 Evolui **todo mês** com novos dados
- 📱 Notifica via **Telegram**
- 📊 Dashboard em **tempo real**
- 🏖️ Roda **24/7** enquanto você está na praia

## 🐉 O Panteão dos Lendários

| # | Lendário | Estratégia | Contas |
|---|----------|------------|--------|
| 1 | 🐉 Necrozma | Mean Reverter | 15 |
| 2 | 🌟 Arceus | [Grande Teste] | 15 |
| 3 | 👻 Giratina | [Grande Teste] | 15 |
| 4 | 💎 Dialga | [Grande Teste] | 15 |
| 5 | 🌊 Palkia | [Grande Teste] | 15 |
| 6 | 🧬 Mew | [Grande Teste] | 15 |
| 7 | ⚡ Rayquaza | [Grande Teste] | 15 |
| 8 | 🔥 Ho-Oh | [Grande Teste] | 15 |
| 9 | ❄️ Lugia | [Grande Teste] | 15 |
| 10 | 🌙 Mewtwo | [Grande Teste] | 15 |
| 11 | ⭐ Celebi | [Grande Teste] | 15 |
| 12 | 🌸 Jirachi | [Grande Teste] | 15 |
| 13 | 🔱 Kyogre | [Grande Teste] | 15 |
| 14 | 💛 Pikachu | Reforço | 5 |

**Total: 200 contas | 14 lendários | Diversificação máxima**

## 🚀 Quick Start

```bash
# Clone o repositório
git clone https://github.com/dans91364-create/NECROZMAv2.git
cd NECROZMAv2

# Instale dependências
pip install -r requirements.txt

# Execute o Grande Teste
python necrozma.py --full 2026-01
```

## 📊 Comandos

```bash
# Grande Teste completo
python necrozma.py --full 2026-01

# Ver ranking atual
python necrozma.py --ranking

# Comparar Bottom 5 vs Top 5
python necrozma.py --compare

# Executar substituições
python necrozma.py --swap

# Gerar relatório
python necrozma.py --report
```

## 📈 Resultados Backtest

### Janeiro 2026 (Necrozma Mean Reverter)
- **Melhor:** +134.97% (Loop 17)
- **Pior:** -46.92% (não quebrou!)
- **Quebras:** 0
- **Cenários positivos:** ~80%

### 5 Anos (2020-2025)
- **Melhor explosão:** +390% (Loop 6, 2025)
- **Nenhuma conta quebrou** com leverage controlada
- **Sistema validado** em todos os cenários de mercado

## 🔄 Sistema Evolutivo

Todo dia 1º do mês:

1. 📥 `git pull` - Atualiza repositório
2. 🚀 `python necrozma.py --full` - Roda Grande Teste
3. 📊 Script baixa dados, converte, testa 288 estratégias
4. 🏆 Gera ranking das 200 contas
5. ⚔️ Compara Bottom 5 vs Top 5 novos
6. 🔄 Substitui fracos por campeões
7. 📱 Notifica Telegram + atualiza Dashboard
8. ☕ **Tempo total: ~1 hora (10 min trabalho real)**

## 🏛️ Arquitetura

```
NECROZMAv2/
├── necrozma.py           # Script principal
├── config.yaml           # Configurações
├── strategies/           # 288 estratégias
│   ├── mean_reverter.py  # 🐉 Necrozma original
│   ├── smc_orderblock.py
│   ├── fibonacci.py
│   └── ...
├── core/                 # Núcleo do sistema
│   ├── downloader.py     # Baixa dados
│   ├── converter.py      # CSV → Parquet
│   ├── backtester.py     # Motor de backtest
│   ├── ranking.py        # Sistema de ranking
│   └── swapper.py        # Substituições
├── data/                 # Dados
│   └── parquet/          # Dados comprimidos
├── results/              # Resultados
├── dashboard/            # Dashboard web
├── telegram/             # Bot Telegram
└── ea/                   # Expert Advisors MT4/MT5
```

## 📱 Telegram + Dashboard

### Notificações
- 📈 Trade aberto/fechado
- 💰 Lucro/Prejuízo
- 📊 Relatório diário
- 🚨 Alertas de emergência

### Comandos
- `/status` - Status geral
- `/balance` - Saldo das contas
- `/ranking` - Top 10 e Bottom 10
- `/report` - Relatório completo

### Dashboard
- Equity curve em tempo real
- Ranking interativo das 200 contas
- Grande Teste integrado
- Substituições com 1 clique

## 💎 A Filosofia

```
"Eu não sei qual vai explodir.
 Mas com 200 contas, 14 lendários, 13 estratégias...
 Eu sei que alguma vai.
 E quando explodir, eu vou estar lá.
 Com meu bilhete premiado.
 Na praia."

                    - O Trainer Necrozma
```

## 📊 Matemática

| Métrica | Valor |
|---------|-------|
| Contas | 200 |
| Lendários | 14 |
| Estratégias | 13 |
| Loops por estratégia | 15 (6-20) |
| Risco por conta | 0.5% do total |
| Investimento inicial | R$40,000 |
| Meta 12 meses | R$214,000+ |
| Renda passiva mensal | R$32,000/mês |

## ⏱️ Tempo de Trabalho

| Período | Tempo |
|---------|-------|
| Por mês | 10 minutos (2 comandos) |
| Por ano | 2 horas |
| Resto | 🏖️ PRAIA |

## 🛡️ Gestão de Risco

- **Diversificação máxima:** 200 contas independentes
- **Leverage controlada:** Nenhuma quebra em 286 cenários testados
- **Seleção natural:** Bottom 5 substituídos todo mês
- **Adaptativo:** Sistema evolui com o mercado

## 🚀 Roadmap

- [x] Conceito e arquitetura
- [x] Backtest Mean Reverter (5 anos)
- [x] Validação Janeiro 2026
- [ ] Implementar 288 estratégias
- [ ] Sistema de ranking automático
- [ ] Bot Telegram
- [ ] Dashboard web
- [ ] Expert Advisors MT4/MT5
- [ ] Deploy VAST.AI
- [ ] 200 contas live
- [ ] 🏖️ PRAIA

---

## 📜 A Lore

*No início, havia apenas uma estratégia. Mean Reverter. Ela lutava sozinha contra o mercado, às vezes vencendo, às vezes perdendo.*

*Mas o Trainer sabia que uma estratégia não era suficiente. Ele precisava de um exército. Um Panteão de Lendários.*

*Assim nasceu o Grande Teste. Uma arena onde 288 estratégias competem. Apenas as mais fortes emergem. Apenas as mais fortes se tornam Lendárias.*

*Necrozma foi o primeiro. O Devorador de Luz. Aquele que transforma a escuridão do mercado em lucro.*

*E assim, um por um, os Lendários foram despertando...*

---

**🐉 NECROZMA v2 - O Devorador de Luz que ilumina o caminho para a praia 🏖️**

*Made with ⚔️ by Trainer Necrozma | 2026*

---

![GitHub](https://img.shields.io/badge/GitHub-NECROZMAv2-black?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Trading](https://img.shields.io/badge/Trading-Automated-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Building-orange?style=for-the-badge)