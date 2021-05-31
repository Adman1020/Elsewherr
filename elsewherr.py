import requests
import re
import time
import yaml

config = yaml.safe_load(open("config.yaml"))
requiredProvidersLower = [re.sub('[^A-Za-z0-9]+', '', x).lower() for x in config["requiredProviders"]]

# Request Headers
radarrHeaders = {'Content-Type': 'application/json', "X-Api-Key":config["radarrApiKey"]}
tmdbHeaders = {'Content-Type': 'application/json'}

# Create all Tags for Providers
for requiredProvider in config["requiredProviders"]:

    providerTag = (config["tagPrefix"] + re.sub('[^A-Za-z0-9]+', '', requiredProvider)).lower()
    newTagJson = {
            'label': providerTag,
            'id': 0
        }
    radarrTagsPost = requests.post(config["radarrUrl"]+'/api/v3/tag', json=newTagJson, headers=radarrHeaders)

# Get all Tags and cretae lists of those to remove and add
radarrTagsGet = requests.get(config["radarrUrl"]+'/api/v3/tag', headers=radarrHeaders)
existingTags = radarrTagsGet.json()
providerTagsToRemove = []
providerTagsToAdd = []

for existingTag in existingTags:
    if config["tagPrefix"].lower() in existingTag["label"]:
        providerTagsToRemove.append(existingTag)
    if str(existingTag["label"]).replace(config["tagPrefix"], '') in requiredProvidersLower:
        providerTagsToAdd.append(existingTag)

# Get all Movies from Radarr
radarrResponse = requests.get(config["radarrUrl"]+'/api/v3/movie', headers=radarrHeaders)
movies = radarrResponse.json()

# Work on each movie
for movie in movies:
    #time.sleep(1)
    print("-------------------------------------------------------------------------------------------------")
    print("Movie: "+movie["title"])
    print("TMDB ID: "+str(movie["tmdbId"]))

    tmdbResponse = requests.get('https://api.themoviedb.org/3/movie/'+str(movie["tmdbId"])+'/watch/providers?api_key='+config["tmdbApiKey"], headers=tmdbHeaders)
    tmdbProviders = tmdbResponse.json()

    # Check that flatrate providers exist for the chosen region
    try:
        providers = tmdbProviders["results"][config["providerRegion"]]["flatrate"]
    except KeyError:
        print("No Flatrate Poviders")
        continue

    # Remove all provider tags from movie
    updateTags = movie.get("tags", [])
    for providerIdToRemove in (providerIdsToRemove["id"] for providerIdsToRemove in providerTagsToRemove):
        try:
            updateTags.remove(providerIdToRemove)
        except:
            continue

    # Add all required providers
    for provider in providers:
        providerName = provider["provider_name"]
        tagToAdd = (config["tagPrefix"] + re.sub('[^A-Za-z0-9]+', '', providerName)).lower()
        for providerTagToAdd in providerTagsToAdd:
            if tagToAdd in providerTagToAdd["label"]:
                print("Adding tag "+tagToAdd)
                updateTags.append(providerTagToAdd["id"])

    update = movie
    update["tags"] = updateTags

    # Update movie in Radarr
    radarrUpdate = requests.put(config["radarrUrl"]+'/api/v3/movie', json=update, headers=radarrHeaders)
    print(radarrUpdate)
    