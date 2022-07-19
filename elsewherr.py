import requests
import re
import time
import yaml
import logging
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const", dest="loglevel", const=logging.DEBUG,
    default=logging.INFO,
)
args = parser.parse_args()    
logging.basicConfig(level=args.loglevel, filename='elsewherr.log', filemode='w', format='%(asctime)s :: %(levelname)s :: %(message)s')

logging.debug('DEBUG Logging Enabled')
logging.debug('Loading Config and setting the list of required Providers')
config = yaml.safe_load(open("config.yaml"))
requiredProvidersLower = [re.sub('[^A-Za-z0-9]+', '', x).lower() for x in config["requiredProviders"]]
logging.debug(f'requiredProvidersLower: {requiredProvidersLower}')

# Request Headers
radarrHeaders = {'Content-Type': 'application/json', "X-Api-Key":config["radarrApiKey"]}
tmdbHeaders = {'Content-Type': 'application/json'}

# Create all Tags for Providers
logging.debug('Create all Tags for Providers within Radarr')
for requiredProvider in config["requiredProviders"]:
    providerTag = (config["tagPrefix"] + re.sub('[^A-Za-z0-9]+', '', requiredProvider)).lower()
    newTagJson = {
            'label': providerTag,
            'id': 0
        }
    logging.debug(f'newTagJson: {newTagJson}')
    radarrTagsPost = requests.post(config["radarrUrl"]+'/api/v3/tag', json=newTagJson, headers=radarrHeaders)
    logging.debug(f'radarrTagsPost Response: {radarrTagsPost}')

# Get all Tags and create lists of those to remove and add
logging.debug('Get all Tags and create lists of those to remove and add')
radarrTagsGet = requests.get(config["radarrUrl"]+'/api/v3/tag', headers=radarrHeaders)
logging.debug(f'radarrTagsGet Response: {radarrTagsGet}')
existingTags = radarrTagsGet.json()
logging.debug(f'existingTags: {existingTags}')
providerTagsToRemove = []
providerTagsToAdd = []

for existingTag in existingTags:
    if config["tagPrefix"].lower() in existingTag["label"]:
        logging.debug(f'Adding tag [{existingTag}] to the list of tags to be removed')
        providerTagsToRemove.append(existingTag)
    if str(existingTag["label"]).replace(config["tagPrefix"], '') in requiredProvidersLower:
        logging.debug(f'Adding tag [{existingTag}] to the list of tags to be added')
        providerTagsToAdd.append(existingTag)

# Get all Movies from Radarr
logging.debug('Getting all Movies from Radarr')
radarrResponse = requests.get(config["radarrUrl"]+'/api/v3/movie', headers=radarrHeaders)
logging.debug(f'radarrResponse Response: {radarrResponse}')
movies = radarrResponse.json()
logging.debug(f'Number of Movies: {len(movies)}')

# Work on each movie
logging.debug('Working on all movies in turn')
for movie in movies:
    update = movie
    #time.sleep(1)
    logging.info("-------------------------------------------------------------------------------------------------")
    logging.info("Movie: "+movie["title"])
    logging.info("TMDB ID: "+str(movie["tmdbId"]))
    logging.debug(f'Movie record from Radarr: {movie}')

    logging.debug("Getting the available providers for: "+movie["title"])
    tmdbResponse = requests.get('https://api.themoviedb.org/3/movie/'+str(movie["tmdbId"])+'/watch/providers?api_key='+config["tmdbApiKey"], headers=tmdbHeaders)
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

    # Remove all provider tags from movie
    logging.debug("Remove all provider tags from movie")
    updateTags = movie.get("tags", [])
    logging.debug(f'updateTags - Start: {updateTags}')
    for providerIdToRemove in (providerIdsToRemove["id"] for providerIdsToRemove in providerTagsToRemove):
        try:
            updateTags.remove(providerIdToRemove)
            logging.debug(f'Removing providerId: {providerIdToRemove}')
        except:
            continue

    # Add all required providers
    logging.debug("Adding all provider tags to movie")
    for provider in providers:
        providerName = provider["provider_name"]
        tagToAdd = (config["tagPrefix"] + re.sub('[^A-Za-z0-9]+', '', providerName)).lower()
        for providerTagToAdd in providerTagsToAdd:
            if tagToAdd in providerTagToAdd["label"]:
                logging.info("Adding tag "+tagToAdd)
                updateTags.append(providerTagToAdd["id"])

    logging.debug(f'updateTags - End: {updateTags}')
    update["tags"] = updateTags
    logging.debug(f'Updated Movie record to send to Radarr: {update}')

    # Update movie in Radarr
    radarrUpdate = requests.put(config["radarrUrl"]+'/api/v3/movie', json=update, headers=radarrHeaders)
    logging.info(radarrUpdate)
    
