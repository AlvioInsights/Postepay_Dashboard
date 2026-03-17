# 📊 Postepay Dashboard Pro

Una dashboard interattiva e locale costruita in Python (Dash/Plotly) per il tracciamento, la categorizzazione automatica e la previsione delle spese bancarie, ottimizzata per gli estratti conto **Postepay** e conti correnti italiani.

---

## 🚀 Prerequisiti e Avvio Veloce

1. Assicurati di avere **Python 3.10+** installato.
2. Clona questo repository sul tuo PC.
3. Apri il terminale nella cartella del progetto e installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
4. Avvia l'applicazione:
   ```bash
   python app.py
   ```
5. Apri il browser all'indirizzo `http://127.0.0.1:8050`

---

## 🛠️ 1. Configurazione Iniziale (Il tuo Storico)

L'applicazione utilizza un file Excel locale come database principale per garantire la tua privacy totale. 
**Nel repository troverai già il file pronto all'uso** nella cartella `data/` chiamato **`dati_finanziari.xlsx`**. Il file è vuoto ma ha già le colonne corrette:

* `Data Contabile`
* `Importo (euro)`
* `Descrizione operazioni`
* `Categoria`

> **⚠️ IMPORTANTE: Il primo "Addestramento"**
> Apri questo file Excel e inserisci manualmente un primo blocco delle tue transazioni passate. **Per questa primissima volta, compila la colonna "Categoria" a mano** (es. *Alimentari, Shopping, Bollette, Stipendio*). 
> Questo passaggio è fondamentale: serve alla dashboard per "imparare" le tue abitudini. Nei caricamenti successivi, **l'app farà tutto da sola** basandosi su questo storico!

---

## 📥 2. Come caricare nuovi movimenti (Es. Postepay)

Quando vuoi aggiornare la dashboard con le nuove spese del mese, scarica l'estratto conto in formato **Excel**  dalla tua banca. 

Se usi **Postepay**, segui questa procedura esatta per preparare il file prima di caricarlo:

1. **Apri il file appena scaricato.**
2. 🧹 **Pulisci il file:**
   * **Elimina l'immagine/logo** di Poste Italiane presente in cima al foglio.
   * **Elimina le prime due righe** di testo (che di solito contengono il saldo contabile o i dati della carta).
   * Assicurati che le intestazioni delle colonne (`Data Contabile`, ecc.) siano diventate la **Riga 1** del tuo foglio Excel.
3. Salva il file pulito.
4. Apri la Dashboard nel browser, e fai **Drag & Drop** (Trascina) il file nel riquadro di caricamento in alto.

✨ *Magia!* La dashboard unirà i nuovi dati al tuo storico, salverà una copia di backup automatica in `data/`, e **assegnerà da sola le categorie** alle nuove spese!

---

## ⚙️ Personalizzazione Avanzata ("Golden Rules")

Vuoi forzare l'app a riconoscere sempre un abbonamento o un negozio specifico, a prescindere dallo storico?
1. Apri il file `src/logic/parser.py`.
2. Cerca il dizionario `self.GOLDEN_RULES`.
3. Aggiungi le tue regole personali. Esempio:
   ```python
   self.GOLDEN_RULES = {
       "NETFLIX": "ABBONAMENTI",
       "ESSELUNGA": "SPESA ALIMENTARE",
       "ENI": "BENZINA"
   }
   ```
La parola a sinistra (in maiuscolo) è quella che l'app cercherà nella causale. La parola a destra è la categoria che verrà assegnata forzatamente.

---

## 🔒 Privacy First
L'app gira interamente in locale (su `localhost`) sul tuo PC. I tuoi dati finanziari, le tue transazioni e i tuoi saldi **non lasciano mai la tua macchina** e non vengono inviati a nessun server esterno. 

---

## 📜 Licenza
Questo progetto è rilasciato sotto licenza **GNU General Public License v3.0 (GPLv3)**. 
Sei libero di scaricare, usare e modificare questo software. Tuttavia, se distribuisci una versione modificata, devi rilasciare il codice sorgente sotto la stessa licenza open source. Maggiori dettagli nel file `LICENSE`.
```
