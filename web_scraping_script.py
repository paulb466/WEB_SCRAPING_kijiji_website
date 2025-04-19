from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime
import psycopg2
import re
import random


# FUNCTIONS

# function for db connection
def db_connection(table):
	try:
		connection = psycopg2.connect(
			host="192.168.2.225",
			port="5445",
			user="username",
			password="password",
			database="postgres_db"
		)
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM public."+table)
		results = cursor.fetchall()
		cursor.close()
		connection.close()
		return results
	except Exception as e:
		print_msg(" - kijiji_search.py - Possible Error with connection to Database - Investigate Python Script - Error is: "+str(e))						# Print error to console
		pass

# function to check for rejected terms
def check_for_keywords(Title, rejected_terms):
	for x in rejected_terms:
		x_as_string = (str(x[0])).strip('[]\'')
		if Title.lower().find(x_as_string) != -1:
			return 1
	return 0

# function to send Telegram msgs
def send_Tlg_msg(message, receiver="paul"):
	try:
		if receiver == "paul":
			TOKEN = "****************"
			chat_id = ###########
		telegram_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
		params = {
			'chat_id': chat_id,
			'text': message,
			'parse_mode': 'HTML',
		}
		response = requests.post(telegram_url, params=params)
	except Exception as e:
		print_msg(" - Possible internet communication error - Could not send Telegram message - Error is: "+str(e))

# function to print to console
def print_msg(message):
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	print(current_time + message)

# function to send 'alive' ping to uptime kuma
def im_alive():
	try:
		response = requests.get("http://192.168.2.225:3005/api/push/jB8wC0Gxuy?status=up&msg=OK&ping=")
		response.close()
	except requests.exceptions.RequestException as e:
		print_msg(f" - Error pinging Uptime Kuma: {e}")
	time.sleep(230)


# DECLARATIONS
dictionaryObject = {}
DictCount = 1
Errors_Web=0
FirstTimeRun = 0

headers = {'Accept': 'text/html, application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
'Accept-Encoding':'gzip, deflate, br',
'Accept-Language':'en-US,en;q=0.5',
'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}





# MAIN LOOP
while True:

	try:

		link_list = db_connection("kijiji_links")			# Get latest Links & Keywords from Database
		random.shuffle(link_list)							# Shuffle link list, so that fb doesnt catch
		rejected_terms = db_connection("rejected_terms")	# Get latest Rejected Terms	from Database

		# LOOP - Go through each database link (kijiji links)

		for x in link_list:

			# print(x)    # FOR TESTING

			# Get refreshed copy of link - has to be inside Main Loop
			# Otherwise youre using the same page that you only pulled once.
			source = requests.get(x[0], headers=headers).text
			soup = BeautifulSoup(source, 'lxml')

			# Get how many items are on the page.
			# So you only search the number of items and get no errors.
			total_num_of_items = int(len(soup.find_all('li',  {'data-testid': re.compile(r'listing\-card\-list\-item\-')})))
			list_of_num_of_items = list(range(0,total_num_of_items))	#List with the number of items on the page, to iterate through

			# Web scrape thru each item on the page
			for count in list_of_num_of_items:

				# Get individual item html code
				item_soup = soup.find('li',  {'data-testid': 'listing-card-list-item-'+str(count)})

				# Get Item information (Title, Location, Description, Price)

				try:	# was getting errors with ads that had no Title
					Title = item_soup.find('h3',  {'data-testid': 'listing-title'}).text.strip()
				except:
					Title = "No Title"
				# print(Title) 		# FOR TESTING


				try:	# was getting errors with ads that had no location
					Location = item_soup.find('p', {'data-testid': 'listing-location'}).span.text.strip()
				except:
					Location = "No Location"


				try:	# was getting errors with ads that had no description
					Desc = item_soup.find('p', {'data-testid': 'listing-description'}).text.strip()
				except:
					Desc = "No Description"


				try:	# was getting errors with ads that had no price
					Price = item_soup.find('p', {'data-testid': 'listing-price'}).text.strip()
				except:
					Price = "No Price"


				try:	# was getting errors with ads that had no link
					Keyword = x[1]
					for a in item_soup.find_all('a', href=True):
						Link = a.get('href')
						break
				except:
					Link = "No Link"


				try:	# SPONSORED
					sponsored = item_soup.find('div', {'data-testid': 'listing-link'}).text.strip()
					sponsored = 1
				except:
					sponsored = 0




				# Check if this is a new item. new item=0, not new item=1
				match = 0
				for b in dictionaryObject:
					if dictionaryObject[b]['Keyword'] == Keyword and dictionaryObject[b]['Title'] == Title and dictionaryObject[b]['Price'] == Price:
						match = 1
						break

				# If it is a new item, and not a sponsored ad run:
				if match == 0 and sponsored == 0:

					# if Keyword.lower().find('free stuff') == -1:	#if free stuff category - check if keywords exist in title that i dont want, 1 keyword is present 0 its not present
					reject_ad = check_for_keywords(Title, rejected_terms)
					# Send Telegram Msg - if this is not the first time running the script AND no rejected keywords in title
					if reject_ad == 0 and FirstTimeRun != 0:
						send_Tlg_msg("Kijiji\n"+Keyword+"\n\n"+Title+"\n"+Price+"\n"+"<a href=\'"+Link+"\'>LINK</a>", x[3])	# Send Telegram message

					# Add new item to Dictionary
					# So it can now be checked against each time it checks an item.
					AddEntry = {(DictCount): {'Title':(Title), 'Price':(Price), 'Keyword':(Keyword)}}
					dictionaryObject.update(AddEntry)
					DictCount+=1

			time.sleep(0.5) #sleep for half a sec before moving on to next kijiji link.  this is so that i dont get booted.

	except Exception as e:
		Errors_Web += 1
		print_msg(" - kijiji_search.py - Possible Error while going through links - Investigate Python Script - Error is: "+str(e))

	# TESTING
	# print(dictionaryObject)




	# Error Reporting
	if Errors_Web > 10:

		# Attempt to send error message thru Telegram.
		# If internet is down which is causing these errors it may not send through.
		try:
			send_Tlg_msg("SCRIPT ERROR \n\n kijiji_search.py - Possible Error with Accessing Website \n\n Investigate Python Script")	# Send Telegram message
		except Exception as e:
			print_msg(" - kijiji_search.py - Possible Error with Internet, could not send Telegram message - Error is: "+str(e))

		# print error to portainer log
		print_msg(" - kijiji_search.py - Possible Error with Accessing Website - Investigate Python Script")

		Errors_Web = 0	# Restart count




	# First time run function.  
	# So that you dont get a huge number of alerts on the first time you run the script.
	# Did it this way so that the number doesnt keep getting unnessarily bigger when adding, just need it to be either 0 or 1.
	if FirstTimeRun == 0:
		FirstTimeRun=1	




	# At 4:30 AM - 4:33 AM clear out the dictionary
	# This is so the dictionary doesnt get too big and bogs down the script.
	# I set it to be done at this time so that there is no real danger of new items getting added at this time.
	current_time = datetime.now().strftime("%H:%M")
	if current_time >= "04:30" and current_time <= "04:50":
		dictionaryObject.clear()
		FirstTimeRun=0




	# Print 'alive' log to console & uptime kuma
	print_msg(" - kijiji_search.py - Script Still Running.")
	im_alive()




	# Sleep before looping thru pages again.  Again random
	current_time = datetime.now().strftime("%H:%M")
	if current_time > "02:00" and current_time < "05:30":
		time.sleep(900)
	else:
		time.sleep(160)