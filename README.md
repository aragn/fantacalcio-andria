# Fantacalcio Andria

Efficient frontier dei giocatori della Lega Fantastico Calcio Andria, stagione 2026/27: volatilità dei voti contro punti per credito pagato.

Sito: https://aragn.github.io/fantacalcio-andria/

## Aggiornare i dati

I file grezzi stanno in `data/raw/` e non sono versionati. Nel sito finiscono solo statistiche derivate (`docs/data.json`).

```bash
python scripts/fetch_votes.py 2026-27 1 10
```

```bash
python scripts/fetch_quotes.py 2026-27
```

```bash
python scripts/build_data.py
```

Le rose vanno lette da Leghe Fantacalcio con il proprio login e salvate in `data/raw/rose_2026-27.txt`, una squadra per riga: `Squadra>>id|ruoli|nome|prezzo;id|ruoli|nome|prezzo`.
