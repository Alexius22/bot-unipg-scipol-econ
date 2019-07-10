"""
ScipolEconPG_Bot - Telegram Bot
Author: Alexius22
"""

import re
import requests
import logging
import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup
from setting import TOKEN, URL
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters, CallbackQueryHandler


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(bot, update):
	#Manda questo messaggio quando il comando /start è invocato
	start_msg = "*Benvenuto a @ScipolEconPG_Bot*\n"\
		"Questo bot ti mostrerà in tempo reale quali lezioni sono presenti nelle aule del Dipartimento di Scienze Politiche ed Economia\n"\
		"Premi il comando /help per visualizzare i comandi\n\n"\
		"_Il bot è da considerarsi NON ufficiale_"
	update.message.reply_markdown(start_msg)

	return ConversationHandler.END

def help_list(bot, update):
	help_msg = "Questa è una lista degli attuali *comandi* presenti nel bot:\n\n"\
			"- /info: Informazioni sul bot e sulla pagina ufficiale GitHub\n\n"\
			"- /orari: Permette di visualizzare gli orari di lezione di un'aula del Dipartimento\n\n"\
			"- /cancel: Annulla un comando in esecuzione"
	update.message.reply_markdown(help_msg)

	return ConversationHandler.END

def info(bot, update):
	info_msg = "*ScipolEconPG* è un comodo metodo per tenerti aggiornato sugli orari "\
				"delle lezioni del Dipartimento di Scienze Politiche ed Economia.*\nL'intero codice sorgente è totalmente open ed è "\
				"consultabile sulla pagina GitHub del creatore di questo bot.*\n\n"
	keyboard = [[InlineKeyboardButton("GitHub", url='https://github.com/Alexius22')]]
	update.message.reply_markdown(info_msg, reply_markup=InlineKeyboardMarkup(keyboard))

	return ConversationHandler.END

def cancel(bot, update):
	#Annulla ogni comando in corso
	update.message.reply_text('Comando annullato', reply_markup=ReplyKeyboardRemove())
	
	return ConversationHandler.END

def orari(bot, update):
	keyboard = [["Oggi"], ["Domani"]]
	date = "Premere su oggi, domani oppure inserire la data nel seguente formato: MM-GG-AA\n\n"\
		"*NB*: _Inserire la data nella formattazione indicata_"

	update.message.reply_markdown(date, reply_markup=ReplyKeyboardMarkup(keyboard))

	return 1

def orari_1(bot, update):
	if update.message.text == "Oggi":
		oggi = datetime.date.today()
		oggi = oggi.strftime("%m-%d-%Y")
		orari_fine(bot, update, oggi)
		
	elif update.message.text == "Domani":
		oggi = datetime.date.today()
		domani = oggi + datetime.timedelta(days=1)
		domani = domani.strftime("%m-%d-%Y")
		orari_fine(bot, update, domani)

	else:
		#Creo un controllo che verifica se il formato inserito per la data dall'utente, è corretto
		controllo = r"^([1-9]|(0)[1-9]|(1)[0-2])((\s)|(\-))([1-9]|[0-2][0-9]|(3)[0-1])((\s)|(\-))(([0-2][0-9])|((20)((0)[0-9]|[1-2][0-9])))$"
		input_utente = update.message.text
		confronto = str(re.match(controllo, input_utente))
		if (confronto == "None"):
			update.message.reply_markdown("Data non corretta, comando annullato.", reply_markup = ReplyKeyboardRemove())
		else:
			fix = re.search(r"match='(.+)>", confronto).group(1)
			orari_fine(bot, update, fix)

	return ConversationHandler.END

#Gestisce i casi in cui non siano ricevuti file di testo e fa il parsing di tutte le informazioni 
def orari_fine(bot, update, text):
	date = text
	date_payload = {'date': date}
	url_payload = requests.get(URL, params=date_payload)

	#Ottengo il plain text della pagina web
	raw = url_payload.text

	#Estraggo la data dell'orario
	data = re.search(r"<h3 align=\"center\">Aule Dipartimento<br/>(.+?) -", raw).group(1)
	data = "*Data lezioni*: " + data + "\n"
	update.message.reply_markdown(data)

	#Estraggo solo la prima tabella
	table = re.search(r"<table width=\"100%\" border=\"0\" cellspacing=\"0\" cellpadding=\"1\"><tr class=\"tableBorder\">([\s\S]+?)</table>", raw).group(1)

	#Ottengo tutte le righe della prima tabella
	all_rows = re.findall(r"<tr class=\"ro[01]\">([\s\S]+?)</tr>", table)

	#Creo stringa vuota da riempire
	stringa = ""
	#stringa = "*Data lezioni*: " + data + "\n"

	for i,row in enumerate(all_rows):
		#Parsing della singola riga
		tds = re.findall(r"<td([\s\S]*?)</td>", row)

		#Ottengo l'aula
		aula = re.search(r"<span class=\"inact\">(.+?)</span>", row).group(1)
		stringa += "\n*Aula*: " + aula +"\n"

		tds.pop(0)
		for td in tds:
			#Ottengo dipartimento
			try:
				dipartimento = re.search(r"event,'(.+?)<br/>", td).group(1)
				dipartimento = dipartimento.replace("Dip.", "*Dipartimento*:")
				dipartimento = dipartimento.replace("SciPol", "Scienze Politiche")
				dipartimento = dipartimento.replace("Scipol", "Scienze Politiche")
				dipartimento = dipartimento.replace("Portineria_sp", "Portineria")
				dipartimento = dipartimento.replace("Portineria_ec Portineria_ec", "Portineria")
				dipartimento = dipartimento.replace("Portineria_ec", "Portineria")
			except AttributeError:
				dipartimento = None
			if (dipartimento == None  or dipartimento == "class=""o"" >&nbsp;"):
				pass
			else:
				stringa += dipartimento + "\n"

			#Ottengo materia	
			try:
				materia = re.search(r"<br/><i>(.+?)</i>'", td).group(1)
				materia = materia.replace("_", " ")
				materia = materia.replace("\\","")
			except AttributeError:
				materia = None
			if (materia == None):
				pass
			elif (materia == "Riservato"):
				stringa += "Aula Riservata\n"
			else:
				stringa += "*Materia*: " + materia + "\n"
			
			#Ottengo orario			
			try:
				#Ottengo il codice univoco di ogni prenotazione
				ind = re.search(r"reserve\('v','','','(.+?)','','0','1','0'\);", td).group(1)
				url_clock = "http://www2.ec.unipg.it/aule/reserve.php?type=v&machid=&start_date=&resid="+ind+"&scheduleid=&is_blackout=0&read_only=1&pending=0&starttime=&endtime="
				clock = requests.get(url_clock)
				clocks = clock.text
				#Parsing e fix dell'orario
				orario = str(re.findall(r"</div>(.+?)</td>", clocks))
				orario = orario.replace("['","*Prenotata* dalle ")
				orario = orario.replace("', '"," alle ")
				orario = orario.replace("']","")
			except AttributeError:
				orario = None
			if(orario == None or dipartimento == None):
				pass
			else:
				stringa += orario + "\n"

		if (i+1) % 7 == 0:
			update.message.reply_markdown(stringa, reply_markup = ReplyKeyboardRemove())
			stringa = ""

	return ConversationHandler.END

def error(bot, update, error):
	#Log Errors caused by Updates
	logging.warning('Update "%s" caused error "%s"' % (update, error))

def main():
	# Creazione dell'EventHandler e settaggio con il proprio token
	updater = Updater(TOKEN)
	dp = updater.dispatcher

	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('help', help_list))
	dp.add_handler(CommandHandler('info', info))
	cmd_orari = ConversationHandler(
        entry_points=[CommandHandler('orari', orari)],

        states={
            1: [MessageHandler(Filters.text, orari_1)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
	dp.add_handler(cmd_orari)
	dp.add_error_handler(error)
	dp.add_handler(CommandHandler('cancel', cancel))


	# Start the bot
	updater.start_polling()
	print("Ready to work")

	# Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()

if __name__ == '__main__':
	main()