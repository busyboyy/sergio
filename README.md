## configurazione
clonare repo ed installare le dipendenze

```bash
git clone https://github.com/busyboyy/sergio.git
cd sergio
pip install -r requirements.txt
```

dopo aver creato un bot telegram con botfather, modificare `config.yaml` inserendo il token del bot:

```yaml
telegram_bot_token: "metti_il_token_qui_senza_togliere_le_virgolette"
```

avviare:

```bash
python main.py
```


## info
ogni gruppo ha la propria catena di Markov salvata in `dati_bot/<chat_id>/total.json`<br>
il livello di ""divertimento"" è salvato in `dati_bot/fun_levels.json`, nel json ci sarà poi l'id del gruppo ed il suo relativo valore<br>
il ""divertimento"" non è nient'altro che la probabilità del bot, in decimi, di rispondere ad un messaggio inviato nel gruppo


## comandi (limitati ai soli admin)

| comando | a cosa serve |
|---|---|
| `/fun` | mosta il divertimento corrente (da 1 a 10) |
| `/fun N` | imposta il divertimento a N, con N numero intero da 1 a 10 |
| `/deletemessage` (rispondendo a un msg) | rimuove quel messaggio dal dizionario del gruppo |
| `/toglimess` | alias di `/deletemessage` |


## dipendenze

- python 3.7+
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- pyYAML
