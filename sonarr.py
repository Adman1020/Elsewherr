import requests
import re
import time
import yaml
import logging
import sys
import argparse
import os

script_directory = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const", dest="loglevel", const=logging.DEBUG,
    default=logging.INFO,
)
args = parser.parse_args()    
logging.basicConfig(
    level=args.loglevel, 
    format='%(asctime)s :: %(levelname)s :: %(message)s',
    handlers=[
        logging.FileHandler(filename=os.path.join(script_directory, 'sonarr.log')),
        logging.StreamHandler()
    ]
)

logging.debug('DEBUG Logging Enabled')
logging.debug('Loading Config and setting the list of required Providers')
config = yaml.safe_load(open(os.path.join(script_directory, 'config.yaml')))
requiredProvidersLower = [re.sub('[^A-Za-z0-9]+', '', x).lower() for x in config["requiredProviders"]]
logging.debug(f'requiredProvidersLower: {requiredProvidersLower}')

# Request Headers
sonarrHeaders = {'Content-Type': 'application/json', "X-Api-Key":config["sonarrApiKey"]}
tmdbHeaders = {'Content-Type': 'application/json'}

logging.debug('Create all Tags for Providers within Sonarr')
for requiredProvider in config["requiredProviders"]:
    providerTag = (config["tagPrefix"] + re.sub('[^A-Za-z0-9]+', '', requiredProvider)).lower()
    newTagJson = {
            'label': providerTag,
            'id': 0
        }
    logging.debug(f'newTagJson: {newTagJson}')
    sonarrTagsPost = requests.post(config["sonarrUrl"]+'/api/v3/tag', json=newTagJson, headers=sonarrHeaders)
    logging.debug(f'sonarrTagsPost Response: {sonarrTagsPost}')

# Get all Tags and create lists of those to remove and add
logging.debug('Get all Tags and create lists of those to remove and add')
sonarrTagsGet = requests.get(config["sonarrUrl"]+'/api/v3/tag', headers=sonarrHeaders)
logging.debug(f'sonarrTagsGet Response: {sonarrTagsGet}')
existingTags = sonarrTagsGet.json()
logging.debug(f'existingTags: {existingTags}')
providerTagsToRemove = []
providerTagsToAdd = []

for existingTag in existingTags:
    if config["tagPrefix"].lower() in existingTag["label"]:
        logging.debug(f'Adding tag [{existingTag}] to the list of tags to be removed')
        providerTagsToRemove.append(existingTag)
    if str(existingTag["label"]).replace(config["tagPrefix"].lower(), '') in requiredProvidersLower:
        logging.debug(f'Adding tag [{existingTag}] to the list of tags to be added')
        providerTagsToAdd.append(existingTag)

# Get all Shows from Sonarr
logging.debug('Getting all Shows from Sonarr')
sonarrResponse = requests.get(config["sonarrUrl"]+'/api/v3/series', headers=sonarrHeaders)
logging.debug(f'sonarrResponse Response: {sonarrResponse}')
shows = sonarrResponse.json()
logging.debug(f'Number of Shows: {len(shows)}')

# Work on each show
logging.debug('Working on all shows in turn')
for show in shows:
    update = show
    #time.sleep(1)
    logging.info("-------------------------------------------------------------------------------------------------")
    logging.info("show: "+show["title"])

    try:
        logging.info("show IMDB ID: "+show["imdbId"])
        imdbSearchResponse = requests.get('https://api.themoviedb.org/3/find/'+str(show["imdbId"])+'?api_key='+config["tmdbApiKey"]+'&language=en-US&external_source=imdb_id', headers=tmdbHeaders)
        logging.debug(f'imdbSearchResponse Response: {imdbSearchResponse}')
        tmdbId = imdbSearchResponse.json()["tv_results"][0]["id"]
        logging.debug('TMDB ID: {tmdbId}')
    except KeyError:
        logging.info("Getting the IMDB failed: " + KeyError)
        continue

    logging.debug(f'Show record from Sonarr: {show}')
    logging.debug("Getting the available providers for: "+show["title"])
    tmdbResponse = requests.get('https://api.themoviedb.org/3/tv/'+str(tmdbId)+'/watch/providers?api_key='+config["tmdbApiKey"], headers=tmdbHeaders)
    logging.debug(f'tmdbResponse Response: {tmdbResponse}')
    tmdbProviders = tmdbResponse.json()
    logging.debug(f'Total Providers: {len(tmdbProviders["results"])}')

    # Check that flatrate providers exist for the chosen region
    logging.debug("Check that flatrate providers exist for the chosen region")
    try:
        providers = tmdbProviders["results"][config["providerRegion"]]["flatrate"]
        logging.debug(f'Flat Rate Providers: {providers}')
    except KeyError:
        logging.info("No Flatrate Providers")
        continue

    # Remove all provider tags from show
    logging.debug("Remove all provider tags from show")
    updateTags = show.get("tags", [])
    logging.debug(f'updateTags - Start: {updateTags}')
    for providerIdToRemove in (providerIdsToRemove["id"] for providerIdsToRemove in providerTagsToRemove):
        try:
            updateTags.remove(providerIdToRemove)
            logging.debug(f'Removing providerId: {providerIdToRemove}')
        except:
            continue

    # Add all required providers
    logging.debug("Adding all provider tags to show")
    for provider in providers:
        providerName = provider["provider_name"]
        tagToAdd = (config["tagPrefix"] + re.sub('[^A-Za-z0-9]+', '', providerName)).lower()
        for providerTagToAdd in providerTagsToAdd:
            if tagToAdd in providerTagToAdd["label"]:
                logging.info("Adding tag "+tagToAdd)
                updateTags.append(providerTagToAdd["id"])

    logging.debug(f'updateTags - End: {updateTags}')
    update["tags"] = updateTags
    logging.debug(f'Updated show record to send to Sonarr: {update}')

    # Update show in Sonarr
    sonarrUpdate = requests.put(config["sonarrUrl"]+'/api/v3/series', json=update, headers=sonarrHeaders)
    logging.info(sonarrUpdate)