# IPBChatScraper
Scraping tool to backup Invision Power Board "Chatbox" messages. Useful for OSINT, quicker data lookup with grep or simply just to have a backup in case forum admins purge the chat history.

Tested with [Chatbox+](https://invisioncommunity.com/files/file/7465-chatbox-free/). Should also work with [Chatbox FREE](https://invisioncommunity.com/files/file/7465-chatbox-free/) but it's currently untested.

## Usage

1. Navigate to the forum chat in your browser, ensure that you're logged in.
2. Open the developer console (F12) and search the sourcecode for "csrfKey". Note down the value. It will look similar to this: bf531df7ef66daef50441d6a08a042fe
3. Open the browser settings and navigate to cookies. Input the forum url and open its cookies.
4. You are looking for "ips4_IPSSessionFront". Note down the value. It will look similar to this: 1f85799402412bf1b30a69b704df46de
5. Lastly note down the url of the chat location. Usually this will be something like https://www.forum.com/index.php
6. Run the scraper with "python3 ipbchatscraper.py -url=https://www.forum.com/index.php -csrf=yourvalue -session=yourvalue"

### Optional Parameters
* **-room=number** Defines the chat room. Default is 1 and will be used when parameter isn't provided.
* **-file=filename** Output filename. Default is chatlog.txt.
* **-continue=number** Continue an aborted backup process from given message id. Will backup the entire chatbox if not given.

### Known bugs
Sometimes the Chat API will claim that the CSRF token is wrong (even though it's not). Resuming the script with the -continue=number option fixes this problem. If you're not sure what the last number was, simply open your output file and check the last added entry. Then add that id to the parameter. I might fix this with an automated retry.
