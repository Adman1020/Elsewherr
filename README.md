**DISCLAIMER: This was thrown together by me late at night with limited python skills. Use it at your own risk. I provide zero warranty. If this nerfs your Radarr library I am really sorry, but theres nothing I can do.**

# Elsewherr
 
**What is it?**

Elsewherr will see if your movies from Radarr are available on a streaming service, and add a tag against the movie if it is.

**How does it work?**

The script will check The Movie Database (https://www.themoviedb.org/) via their API, which in turn uses Just Watch (https://www.justwatch.com/), to get all streaming services each movie is on. If it matches one of your chosen list to monitor, it then adds this tag in Radarr.

**Why?**

Why not? What you do with this information is up to you. You might want to remove movies that are on Netflix to save space, or just like to know theres an option availble other than your local library. 

**How do I use it?**
- Download, clone, or otherwise obtain this repo and put it somewhere
- Run `python -m pip install -r requirements.txt` or `pip -r requirements.txt`
- Get an account at TMDb (https://www.themoviedb.org/) and grab an API key
- Rename `config.yaml.example` to `config.yaml`
- Edit `config.yaml` as per the table below
- Run `python elsewherr.py`, or `run.bat` to run the script.

You might want to setup a scheduled task or something to run this regularly to keep the list up to date as moves are added to or drop off streaming services.

**Parameters**

|Parameter|Description|
|---|---|
|tmdbApiKey|API Key for The Movie Database|
|providerRegion|2 digit region code to use to check the availability of movies on that regions streaming service. The `providers.txt` file contains a list of codes|
|radarrApiKey|Your API key for Radarr|
|radarrUrl|Full URL including port to Radarr|
|requiredProviders|List of the providers you would like to search for. Providers must be entered *exactly* as they appear in the Providers list from TMDb to work. |
|tagPrefix|Prefix that will be included in the tags added to Radarr|

A list of Regions and Providers is available in `providers.txt`, but you can also run the `providers.py` script to grab an up to date list. 

**Note:** The prefix is important, its used to remove all tags before re-adding to catch movies being removed from services. If you don't use a prefix, this script will remove all your tags from your movies. You can change it from the default *elsewherr-*, just make sure its unique.


