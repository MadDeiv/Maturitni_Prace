# Maturitní práce – zjednodušená kryptoměna

Jednoduchý vzdělávací prototyp kryptoměny založený na blockchainu, vytvořený v Pythonu s frameworkem Flask, určený k demonstraci základních principů blockchainu, jako jsou peněženky, transakce a těžba s proof of work.

---

## Popis

Tato webová aplikace byla vytvořena jako maturitní práce na téma blockchain a kryptoměny. Umožňuje uživatelům:
- Vytvářet peněženky s kryptografickými klíči ECDSA.
- Kontrolovat zůstatek peněženek.
- Odesílat podepsané transakce mezi peněženkami.
- Těžit bloky pomocí proof of work s pevnou obtížností 4.
- Ukládat a načítat stav blockchainu do/ze souborů JSON.

Projekt napodobuje některé prvky Bitcoinu (řetězení bloků, podpis transakcí, těžba), ale je centralizovaný a zjednodušený pro vzdělávací účely. Neobsahuje pokročilé funkce, jako je dynamická obtížnost, a je určen k pochopení základů blockchainu na jednom serveru.

---

## Instalace

### Požadavky
- Python 3.6 nebo vyšší
- pip (správce balíčků Pythonu)
- Flask (webový framework)
- ECDSA (knihovna pro kryptografické operace)

### Kroky
1. **Klonování repozitáře**  
   Stáhněte si projekt z GitHubu:
   ```bash
   git clone https://github.com/MadDeiv/Maturitni_Prace.git
   cd Maturitni_Prace
