import requests
import os
import yaml

script_directory = os.path.dirname(os.path.abspath(__file__))
config = yaml.safe_load(open(os.path.join(script_directory, 'config.yaml')))

tmdbHeaders = {'Content-Type': 'application/json'}

tmdbResponseRegions = requests.get('https://api.themoviedb.org/3/watch/providers/regions?api_key='+config["tmdbApiKey"], headers=tmdbHeaders)
tmdbRegions = tmdbResponseRegions.json()

tmdbResponseProviders = requests.get('https://api.themoviedb.org/3/watch/providers/movie?api_key='+config["tmdbApiKey"], headers=tmdbHeaders)
tmdbProviders = tmdbResponseProviders.json()

with open(os.path.join(script_directory, 'res', 'regions.txt'), 'w', encoding='utf-8') as f:
    for result in tmdbRegions['results']:
        f.write(f"{result['iso_3166_1']}\t{result['english_name']}\n")

with open(os.path.join(script_directory, 'res', 'providers.txt'), 'w', encoding='utf-8') as f:
    for result in sorted(set(p['provider_name'] for p in tmdbProviders['results'])):
        f.write(f"{result}\n")
