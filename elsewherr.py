import argparse
import logging
import os
import re
from pyarr import SonarrAPI, RadarrAPI
from tmdbv3api import TMDb, Find, Movie, TV
import yaml

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Set log level to debug.')
    parser.add_argument('-l', '--log-to-file', action='store_true', help='Enable logging to file. (logs\elsewherr.log)')

    return parser.parse_args()

def setup(args):
    global config
    global logger
    
    dir = os.path.dirname(os.path.abspath(__file__))
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s :: %(levelname)s :: %(message)s',
        handlers=list(filter(None, [
            logging.FileHandler(filename=os.path.join(dir, 'logs', 'elsewherr.log')) if args.log_to_file else None,
            logging.StreamHandler()
        ]))
    )

    logger = logging.getLogger('elsewherr')
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    logger.info('Elsewherr starting.')
    logger.debug('DEBUG Logging Enabled')
    logger.debug('Loading Config and setting the list of required Providers')
    config = yaml.safe_load(open(os.path.join(dir, 'config.yaml')))
    logger.debug(config)

    tmdb = TMDb()
    tmdb.api_key = config['tmdb']['api_key']

def get_tag_label_for_provider(provider_name):
    return f"{config['prefix']}{re.sub('[^A-Za-z0-9]+', '', provider_name)}".lower()

def process_radarr():
    radarr = RadarrAPI(host_url=config['radarr']['url'], api_key=config['radarr']['api_key'])
    movies = radarr.get_movie()

    for provider in config['providers']:      
        response = radarr.create_tag(get_tag_label_for_provider(provider))
        logger.debug('Response: %s' % response)

    all_tags = radarr.get_tag()
    tags_id_to_label = dict((tag['id'], tag['label']) for tag in all_tags)
    tags_label_to_id = dict((tag['label'], tag['id']) for tag in all_tags)

    for movie in movies:
        try:
            logger.debug('--------------------------------------------------')
            logger.debug('Movie: %s' % movie['title'])
            logger.debug(f"Existing Tags: {', '.join(map(lambda x: tags_id_to_label.get(x), movie['tags'])) if len(movie['tags']) > 0 else 'None'}")
            tags_list = list(filter(lambda x: not tags_id_to_label.get(x).startswith(config['prefix'].lower()), movie['tags']))

            providers = Movie().watch_providers(movie['tmdbId'])['results'].get(config['tmdb']['region'], {}).get('flatrate', [])
            for provider in providers:
                provider_name = provider['provider_name']

                if provider_name in config['providers']:
                    logger.debug('Adding provider: %s' % provider_name)
                    tags_list.append(tags_label_to_id.get(get_tag_label_for_provider(provider_name)))
                else:
                    logger.debug('Skipping provider: %s' % provider_name)

            logger.debug(f"Resultant Tags: {', '.join(map(lambda x: tags_id_to_label.get(x), tags_list)) if len(tags_list) > 0 else 'None'}")
            movie['tags'] = tags_list
            radarr.upd_movie(movie)
        except Exception as e:
            logger.error(e)
            logger.error('Failed to process movie %s' % movie['title'])
            continue

    logger.debug('--------------------------------------------------')
    logger.info('Processed %i movies.' % len(movies))

def process_sonarr():
    sonarr = SonarrAPI(host_url=config['sonarr']['url'], api_key=config['sonarr']['api_key'])
    all_series = sonarr.get_series()

    for provider in config['providers']:      
        response = sonarr.create_tag(get_tag_label_for_provider(provider))
        logger.debug('Response: %s' % response)

    all_tags = sonarr.get_tag()
    tags_id_to_label = dict((tag['id'], tag['label']) for tag in all_tags)
    tags_label_to_id = dict((tag['label'], tag['id']) for tag in all_tags)
    
    for series in all_series:
        try:
            logger.debug('--------------------------------------------------')
            logger.debug('Series: %s' % series['title'])
            logger.debug(f"Existing Tags: {', '.join(map(lambda x: tags_id_to_label.get(x), series['tags'])) if len(series['tags']) > 0 else 'None'}")

            result = Find().find_by_tvdb_id(str(series['tvdbId']))
            tmdb_id = result['tv_results'][0]['id']
            logger.debug('Found TMDB ID: %s' % tmdb_id)

            tags_list = list(filter(lambda x: not tags_id_to_label.get(x).startswith(config['prefix'].lower()), series['tags']))

            providers = TV().watch_providers(tmdb_id)['results'][config['tmdb']['region']].get('flatrate', [])
            for provider in providers:
                provider_name = provider['provider_name']

                if provider_name in config['providers']:
                    logger.debug('Adding provider: %s' % provider_name)
                    tags_list.append(tags_label_to_id.get(get_tag_label_for_provider(provider_name)))
                else:
                    logger.debug('Skipping provider: %s' % provider_name)

            logger.debug(f"Resultant Tags: {', '.join(map(lambda x: tags_id_to_label.get(x), tags_list)) if len(tags_list) > 0 else 'None'}")
            series['tags'] = tags_list
            sonarr.upd_series(series)
        except Exception as e:
            logger.error(e)
            logger.error('Failed to process series %s' % series['title'])
            continue

    logger.debug('--------------------------------------------------')
    logger.info('Processed %i series.' % len(all_series))

def execute():
    setup(get_args())
    
    if config['radarr']['enabled']:
        process_radarr()
    
    if config['sonarr']['enabled']:
        process_sonarr()

    logger.info('Elsewherr completed.')

if __name__ == '__main__':
    execute()
