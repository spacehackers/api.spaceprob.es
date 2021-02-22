scraper runs on heroku scheduler

----
(is this still used?) --> wolphramalpha.py

initializes the database with data from wolphram alpha for each spacecraft in list_active_probes.txt. This will replace any older data for each key!

Redis keys are spacecraft names. Spaces are replaced with underscores (since probe names may have legit dash)

all wolframalpha data is stored in the key 'wolframalpha'
