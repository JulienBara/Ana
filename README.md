# Ana
Ana is a bot for Telegram. Her aim is to learn standard answers to standard questions by reading the conversations she is in. 
As she learns from reading, she can answer standard answers.


Installation
------------

* First clone the repository :
  `$ git clone https://github.com/JulienBara/Ana.git`

* Create the `key` file at the root of the project :
  `$ echo "<MY_TELEGRAM_BOT>" > key`

  If you don't know what it is, visit this link https://core.telegram.org/bots. You can get a key from BotFather.

* Create the `father` file at the root of the project :
  `$ echo "<MY_TELEGRAM_USER_ID>" > father`

* Install `python3` et `pip3` si tu les as pas. Bon là tu te débrouilles parce que quand même tu es grand.

* Install dependancies :
  `pip3 install -r requirements.txt`

* Execute the bot :
  `python3 anav2/ana.py`

* In the Telegram chat with Ana, write the init command to make Ana create her database if necessary :
  `/startAna`

* Ana is ready to learn and talk !


Settings
-------
* If you find that Ana talk too much and what she says isn't accurate enough, you can increase the accuracy number. Default value is 1.0. You have to be her father. :
  `/updateAccuracyNumber <YOUR NEW NUMBER>`


Versions
------------
* Anav2 works by learning at each message. Everytime she gets a message, she remembers this message as the "Winning Message" and the few messages before as "Trigger Message" with Weight decreasing
as the message is far from the Winning Message. When she read a message, she tries to answer with a corresponding Winning Message she knows. There is also some randomness to make her unpredictable ;)

* Anav1 works with a list of hardcoded messages known as "Victory Messages" (e.g. a message containing "Haha" or "Ana"). When one of this message is triggered. 
Ana remember the message just before as the "Winning Message" because it led to the "Victory Message". The few messages before are remembered as "Trigger Message" because they are the ones that may
 trigger the "Winning Message". When Ana read a message that looks like a "Trigger Message" she answers with a "Winning Message" associated with this "Trigger Message".




Licence
-------

Ana is under PDBPL license. More information [here](http://license.picdeballmer.science).

