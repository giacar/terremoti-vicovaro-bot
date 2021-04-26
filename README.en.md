# Vicovaro Earthquake Bot
[![it](https://img.shields.io/badge/lang-it-green.svg)](https://github.com/giacar/terremoti-vicovaro-bot/blob/main/README.md)
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/giacar/terremoti-vicovaro-bot/blob/main/README.en.md)

Vicovaro Earthquake Bot is a Telegram bot that allows to monitor seismic events occuring in ​​Vicovaro (RM) and surroundings, exploiting directly INGV [API](http://terremoti.ingv.it/webservices_and_software). In this way it's possible to be notified in real time about new events and to see those that have already occurred.
In particular, it was been created in conjunction with the seismic swarm that took place between December 2020 and January 2021, news: [RomaToday](https://www.romatoday.it/cronaca/terremoto-roma-est-28-gennaio-2021.html).

## Telegram link
The bot can be used [clicking here](https://t.me/vicovaro_earthquakes_bot).

## Language
The application is written in Python, in particular using the [Telepot](https://telepot.readthedocs.io/en/latest/) library in order to take advantage of all the available functions. In addition there is also a Postgres database to store some essential information for the its functioning. Everything is hosted on the [Heroku](https://www.heroku.com/) platform.

## Functionality
The bot allows you to take advantage of the following features:
* Notifications in real time on new seismic events in the area recorded by INGV, with the possibility of disabling them.
* Display of the last, all or part of the events that occurred in the last 2 months in the area.
* Each seismic event is accompanied by all the necessary information, with a link to the INGV page and a map to be able to locate it.

## To Do
No new features are currently planned, for suggestions you can open an issue from [here](https://github.com/giacar/terremoti-vicovaro-bot/issues).

## Donation
If the bot was useful to you and you want to support me, you can do it by making me a PayPal donation [clicking here](https://www.paypal.me/gianmarcocariggi). Thank you for the support!