# Terremoti Vicovaro Bot
[![it](https://img.shields.io/badge/lang-it-green.svg)](https://github.com/giacar/terremoti-vicovaro-bot/blob/main/README.md)
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/giacar/terremoti-vicovaro-bot/blob/main/README.en.md)

Terremoti Vicovaro Bot è un bot Telegram che permette di monitorare gli eventi sismici che accadono nella zona di Vicovaro (RM) e dintorni sfruttando direttamente le [API](http://terremoti.ingv.it/webservices_and_software) dell'INGV. In questo modo è sia possibile essere notificato in tempo reale sui nuovi eventi, che visualizzare quelli già accaduti.
In particolare, è stato creato in concomitanza con lo sciame sismico avvenuto tra Dicembre 2020 e Gennaio 2021, notizia: [RomaToday](https://www.romatoday.it/cronaca/terremoto-roma-est-28-gennaio-2021.html).

## Link Telegram
Il bot può essere utilizzato [cliccando qui](https://t.me/vicovaro_earthquakes_bot).

## Linguaggio
L'applicazione è scritta in Python, in particolare usando la libreria [Telepot](https://telepot.readthedocs.io/en/latest/) per poter sfruttare tutte le funzioni messe a disposizione. Inoltre è presente anche un database Postgres per poter memorizzare alcune informazioni essenziali per il funzionamento dello stesso. Il tutto è hostato sulla piattaforma [Heroku](https://www.heroku.com/).

## Funzionalità
Il bot permette di sfruttare le seguenti funzionalità:
* Notifiche in tempo reale sui nuovi eventi sismici della zona registrati da INGV, con possibilità di disattivarle.
* Visualizzazione dell'ultimo, di tutti o di una parte degli eventi accaduti negli ultimi 2 mesi in zona.
* Ogni evento sismico è accompagnato da tutte le informazioni necessarie, con un link alla pagina di INGV e una mappa per poterlo localizzare.

## To Do
Attualmente non è in programma nessuna nuova funzionalità, per suggerimenti è possibile aprire un issue da [qui](https://github.com/giacar/terremoti-vicovaro-bot/issues).

## Donazione
Se il bot ti è stato utile e vuoi supportarmi, puoi farlo facendomi una donazione PayPal [cliccando qui](https://www.paypal.me/gianmarcocariggi). Grazie per il supporto!