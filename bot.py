import urllib.request
from urllib.error import URLError, HTTPError
import time
import sys
import os
from io import StringIO, BytesIO
import pandas as pd
import logging
import signal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone
import psycopg2

import telepot
from telepot.loop import MessageLoop

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s [%(funcName)s] %(message)s', datefmt='%Y-%m-%d,%H:%M:%S', level=logging.INFO)

PREVIOUS_MONTHS = -2
PREVIOUS_NUM = 10

# REQUEST PARAMETERS
STARTTIME=str(date.today()+relativedelta(months=PREVIOUS_MONTHS))            # all events happened PREVIOUS_MONTHS months ago since today
MINMAG="0"
LAT="42.02"
LON="12.89"
MAXRADIUSKM="20"

# http://webservices.ingv.it/fdsnws/event/1/query?starttime=2020-12-29&minmag=0&lat=42.02&lon=12.89&maxradiuskm=20&format=text
URL = "http://webservices.ingv.it/fdsnws/event/1/query?starttime="+STARTTIME+"&minmag="+MINMAG+"&lat="+LAT+"&lon="+LON+"&maxradiuskm="+MAXRADIUSKM+"&format=text"

DONATION = os.environ.get("DONATION", None)

TOKEN = os.environ.get("TOKEN_BOT", None)
DATABASE_URL = os.environ.get("DATABASE_URL", None)

chat_id_dict = {}

def handle_SIGTERM(sig, frame):
    logging.info("Updating database before to exit...")
    cur = conn.cursor()

    for key in list(chat_id_dict):
        for id in chat_id_dict[key]:
            if key == 'active':
                cur.execute("UPDATE chat_id SET active = %s WHERE id = %s;", (True, id))
            else:
                cur.execute("UPDATE chat_id SET active = %s WHERE id = %s;", (False, id))

    conn.commit()

    cur.close()
    conn.close()

    logging.info("Database updated, now I can exit safely")
    sys.exit(0)

def fromChatIDToDB(id, active):
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM chat_id WHERE id = %s;", (id,))
    if len(cur.fetchall()) == 0:
        cur.execute("INSERT INTO chat_id(id, active) VALUES (%s, %s);", (id, active))
    else:
        cur.execute("UPDATE chat_id SET active = %s WHERE id = %s;", (active, id))

    conn.commit()
    cur.close()

def fromDBToChatID():
    cur = conn.cursor()

    dict_ids = {
        'active':[],
        'stopped':[]
    }
    
    cur.execute("SELECT * FROM chat_id;")
    list_ids = cur.fetchall()

    for tuple in list_ids:
        if tuple[1] == True:
            dict_ids['active'].append(tuple[0])
        else:
            dict_ids['stopped'].append(tuple[0])

    cur.close()
    return dict_ids

def getINGV():
    try:
        response = urllib.request.urlopen(URL)
    
        if response.getcode() == 200:
            contents = response.read().decode("utf-8")
            return contents
        else:
            return -1
    except HTTPError as e:
        logging.error("Error code: "+str(e.code))
        return -1
    except URLError as e:
        logging.error("Reason: "+str(e.reason))
        return -1

def initTable():
    FILETXT = None

    s = getINGV()
    if s.isdigit():
        logging.warn("Not possible to GET Data")
        return -1
    else:
        FILETXT = StringIO(s)

    df = pd.read_csv(FILETXT, sep='|')

    return df

def updateTable(table):
    s = getINGV()
    if s.isdigit():
        logging.warn("Not possible to GET Data")
        return (-1, -1)
    else:
        FILETXT = StringIO(s)

    newdf = pd.read_csv(FILETXT, sep='|')

    diffdf = pd.merge(table, newdf, how='outer', indicator='Exist')
    diffdf = diffdf.loc[diffdf['Exist'] == 'right_only']                # new events (events only in newdf)
    
    return (newdf, diffdf)

def realNewEvent(event):
    rawtimestamp = str(event['Time'])                                   #2021-01-23T13:09:56.000000
    rawdate = rawtimestamp.split('T')[0]                                #2021-01-23

    eventdate = date.fromisoformat(rawdate)
    todaydate = datetime.now(timezone('Europe/Rome')).date()            # get Italy's date to fix if server is hosted in other countries

    if eventdate == todaydate:
        return True
    return False

def buildMessage(event):
    logging.debug(event)

    # extract time information
    rawtimestamp = str(event['Time'])                                   #2021-01-23T13:09:56.000000
    rawdate = rawtimestamp.split('T')[0].split('-')                     #[2021,01,23]
    year = rawdate[0]
    month = rawdate[1]
    day = rawdate[2]
    time = rawtimestamp.split('T')[1].split('.')[0].split(':')          #[13,09,56]
    hour = time[0]
    minute = time[1]
    second = time[2]

    locationname = event['EventLocationName'].replace('(', '\(').replace(')', '\)')
    latitude = ('%.4f'%float(event['Latitude'])).replace('.', '\.')
    longitude = ('%.4f'%float(event['Longitude'])).replace('.', '\.')
    depth = str(event['Depth/Km']).replace('.', '\.')
    magnitude = str(event['Magnitude']).replace('.', '\.')
    link = "http://cnt.rm.ingv.it/event/"+str(event['#EventID'])

    message = "Terremoto alle %s:%s del %s/%s/%s " %(hour, minute, day, month, year)
    message = message + "\n\n"
    message = message + "Epicentro: %s \nCoordinate: %s, %s \n\nProfondità: %s km \nMagnitudo: %s \nLink INGV: [clicca qui](%s)" %(locationname, latitude, longitude, depth, magnitude, link)
    
    logging.debug(message)

    return message

def sendNewEvents(newevents):
    logging.info("Sending new events to subscribers...")
    neweventsback = newevents.iloc[::-1]                # reverse in order to send from older to newer
    for id in chat_id_dict['active']:
        for index, event in neweventsback.iterrows():
            if realNewEvent(event):                     # check if the event happens today to avoid fake new event
                message = buildMessage(event)

                bot.sendMessage(id, message, parse_mode="MarkdownV2", disable_web_page_preview=True)
                bot.sendLocation(id, float(event['Latitude']), float(event['Longitude']))
    del neweventsback
    logging.info("Sending completed")

def handleMessageBot(msg):
    chat_id = msg['chat']['id']
    msg_cont = msg['text'].lower()
    
    if msg_cont == '/start' :
        if chat_id not in chat_id_dict['active'] and chat_id not in chat_id_dict['stopped']:             # new user
            chat_id_dict['active'].append(chat_id)
            fromChatIDToDB(chat_id, True)
            logging.info("New Chat: " + str(chat_id))
            bot.sendMessage(chat_id, "Benvenuto! Riceverai un messaggio appena ci sarà un nuovo evento sismico")
        
        elif chat_id not in chat_id_dict['active'] and chat_id in chat_id_dict['stopped']:               # old user: enable notification
            chat_id_dict['active'].append(chat_id)
            chat_id_dict['stopped'].remove(chat_id)
            fromChatIDToDB(chat_id, True)
            logging.info("Active Chat: " + str(chat_id))
            bot.sendMessage(chat_id, "Bentornato! Riceverai un messaggio appena ci sarà un nuovo evento sismico")
        
        else:
            bot.sendMessage(chat_id, "Le notifiche sono già attive")
    
    if msg_cont == '/ultimo' :
        df = initTable().head(1)

        if len(df) == 0:
            bot.sendMessage(chat_id, "Nessun evento sismico negli ultimi %d mesi"%PREVIOUS_MONTHS)
        else:
            bot.sendMessage(chat_id, "Ecco l'ultimo evento sismico ad oggi:")
            for index, event in df.iterrows():
                message = buildMessage(event)

                bot.sendMessage(chat_id, message, parse_mode="MarkdownV2", disable_web_page_preview=True)
                bot.sendLocation(chat_id, float(event['Latitude']), float(event['Longitude']))

        del df
    
    if msg_cont == '/ultimi' :
        df = initTable().head(PREVIOUS_NUM)         # last PREVIOUS_NUM events
        
        if len(df) == 0:
            bot.sendMessage(chat_id, "Nessun evento sismico negli ultimi %d mesi"%PREVIOUS_MONTHS)
        else:
            dfback = df.iloc[::-1]                      # reverse the sending order

            bot.sendMessage(chat_id, "Ecco gli ultimi %d eventi sismici ad oggi:"%PREVIOUS_NUM)
            for index, event in dfback.iterrows():
                message = buildMessage(event)

                bot.sendMessage(chat_id, message, parse_mode="MarkdownV2", disable_web_page_preview=True)
                bot.sendLocation(chat_id, float(event['Latitude']), float(event['Longitude']))

            del dfback
        
        del df
    
    if msg_cont == '/tutti' :
        df = initTable()                # all the events

        if len(df) == 0:
            bot.sendMessage(chat_id, "Nessun evento sismico negli ultimi %d mesi"%PREVIOUS_MONTHS)
        else:
            dfback = df.iloc[::-1]          # reverse the sending order

            bot.sendMessage(chat_id, "Ecco tutti gli eventi sismici dal 29/12/2020 ad oggi:")
            for index, event in dfback.iterrows():
                message = buildMessage(event)

                bot.sendMessage(chat_id, message, parse_mode="MarkdownV2", disable_web_page_preview=True)
                bot.sendLocation(chat_id, float(event['Latitude']), float(event['Longitude']))
            
            del dfback

        del df
    
    if msg_cont == '/stop' :
        if chat_id in chat_id_dict['active']: chat_id_dict['active'].remove(chat_id) 
        chat_id_dict['stopped'].append(chat_id)
        fromChatIDToDB(chat_id, False)
        bot.sendMessage(chat_id, "Le notifiche sono state disattivate, puoi riattivarle in ogni momento attraverso il comando /start")
        logging.info("Deactive Chat: " + str(chat_id))

    if msg_cont == '/dona':
        donation_msg = "Se il bot ti piace e vuoi supportarmi, puoi farmi una donazione tramite PayPal [cliccando qui](%s)\. Grazie\!"%DONATION
        bot.sendMessage(chat_id, donation_msg, parse_mode="MarkdownV2", disable_web_page_preview=True)



conn = psycopg2.connect(DATABASE_URL, sslmode='require')

signal.signal(signal.SIGTERM, handle_SIGTERM)

bot = telepot.Bot(TOKEN)

chat_id_dict = fromDBToChatID()                           # load the chat IDs from old epochs
logging.info("Recovered %d previous active subscriber(s)"%len(chat_id_dict['active']))
logging.info("Recovered %d previous inactive subscriber(s)"%len(chat_id_dict['stopped']))

MessageLoop(bot, handleMessageBot).run_as_thread()

# TEST
#time.sleep(10)


# Initialize the table
df = initTable()
while isinstance(df, int) and df==-1:
    df = initTable()

logging.info("Table initialized")

# TEST
#logging.info("Testing mode, please ignore the first fake event")
#df = df.drop(3)

i = 0

# Loop
while (True):
    if i==60:
        logging.info("Number of total subscribers: %d; active: %d, inactive: %d."%(len(chat_id_dict['active'])+len(chat_id_dict['stopped']), len(chat_id_dict['active']), len(chat_id_dict['stopped'])))
        i=0

    newdf, diffdf = updateTable(df)

    if isinstance(newdf, int) and isinstance(diffdf, int) and (newdf, diffdf) == (-1, -1):
        time.sleep(10)
        continue

    if len(diffdf)>0:
        logging.info("New event(s) found!")
        sendNewEvents(diffdf)

    del df
    df = newdf

    i+=1
    time.sleep(60)
