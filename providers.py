import requests
import os
import yaml

config = yaml.safe_load(open("config.yaml"))

try:
    os.remove("providers.txt")
except:
    pass

tmdbHeaders = {'Content-Type': 'application/json'}

tmdbResponseRegions = requests.get('https://api.themoviedb.org/3/watch/providers/regions?api_key='+config["tmdbApiKey"], headers=tmdbHeaders)
tmdbRegions = tmdbResponseRegions.json()

tmdbResponseProviders = requests.get('https://api.themoviedb.org/3/watch/providers/movie?api_key='+config["tmdbApiKey"], headers=tmdbHeaders)
tmdbProviders = tmdbResponseProviders.json()
allProviders = []
for p in tmdbProviders["results"]:
    allProviders.append(p["provider_name"])
providers = sorted(set(allProviders))


f = open("providers.txt", "a")
f.write("Regions\n-------\n")
for r in tmdbRegions["results"]:
    f.write(str(r["iso_3166_1"])+"\t"+str(r["english_name"])+"\n")
f.write("\n\nProviders\n---------\n")
for p in providers:
    f.write(str(p)+"\n")
f.close()


