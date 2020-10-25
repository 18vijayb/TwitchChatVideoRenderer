import argparse
import os
from pathlib import Path
from typing import List, Callable

import requests

from arguments import Arguments
from downloader import Downloader
from logger import Logger, Log
from tcdsettings import Settings

__name__: str = 'tcd'
__version__: str = '3.2.0'
__all__: List[Callable] = [Arguments, Settings, Downloader, Logger, Log]


def main():
    # Arguments
    parser = argparse.ArgumentParser(description=f'Twitch Chat Downloader {__version__}')
    parser.add_argument('-v', f'--{Arguments.Name.VIDEO}', type=str, help='Video IDs separated by commas')
    parser.add_argument('-c', f'--{Arguments.Name.CHANNEL}', type=str, help='Channel names separated by commas')
    parser.add_argument('-u', f'--{Arguments.Name.USER}', type=str, help='Messages from users, separated by commas')
    parser.add_argument(f'--{Arguments.Name.FIRST}', type=int, default=5, help='Download chat from the last n VODs')
    parser.add_argument(f'--{Arguments.Name.CLIENT_ID.replace("_", "-")}', type=str, help='Twitch client ID')
    parser.add_argument(f'--{Arguments.Name.CLIENT_SECRET.replace("_", "-")}', type=str, help='Twitch client secret')
    parser.add_argument(f'--{Arguments.Name.VERBOSE}', action='store_true', help='Verbose output')
    parser.add_argument('-q', f'--{Arguments.Name.QUIET}', action='store_true')
    parser.add_argument('-o', f'--{Arguments.Name.OUTPUT}', type=str, help='Output directory', default='./')
    parser.add_argument('-f', f'--{Arguments.Name.FORMAT}', type=str, help='Message format', default='default')
    parser.add_argument(f'--{Arguments.Name.TIMEZONE}', type=str, help='Timezone name')
    parser.add_argument(f'--includes', type=str, help='Messages must include specified text')
    parser.add_argument(f'--{Arguments.Name.INIT}', action='store_true', help='Script setup')
    parser.add_argument(f'--{Arguments.Name.VERSION}', action='store_true', help='Settings version')
    parser.add_argument(f'--{Arguments.Name.FORMATS}', action='store_true', help='List available formats')
    parser.add_argument(f'--{Arguments.Name.PREVIEW}', action='store_true', help='Preview output')
    parser.add_argument(f'--{Arguments.Name.SETTINGS}', action='store_true', help='Preview output')
    parser.add_argument(f'--{Arguments.Name.SETTINGS_FILE.replace("_", "-")}', type=str,
                        default=str(Path.home()) + '/.config/tcd/settings.json',
                        help='Settings file location')
    parser.add_argument(f'--{Arguments.Name.DEBUG}', action='store_true', help='Print debug messages')
    parser.add_argument(f'--{Arguments.Name.LOG}', action='store_true', help='Save log file')
    parser.add_argument(f'--{Arguments.Name.START_TIME}', type=int, help='Start time in twitch vod')
    parser.add_argument(f'--{Arguments.Name.VIDEO_LENGTH}', type=int, help='Uploaded video length')

    Arguments(parser.parse_args().__dict__)
    Settings(Arguments().settings_file,
             reference_filepath=f'{os.path.dirname(os.path.abspath(__file__))}/settings.reference.json')

    # Print version number
    if Arguments().print_version:
        Logger().log(f'Twitch Chat Downloader {__version__}', retain=False)
        return

    # Print settings file location
    if Arguments().settings:
        Logger().log(str(Settings().filepath))
        return

    # Client ID
    Settings().config['client_id'] = Arguments().client_id or Settings().config.get('client_id', None) or input(
        'Twitch client ID: ').strip()
    Settings().config['client_secret'] = Arguments().client_secret or Settings().config.get('client_secret', None) or input(
        'Twitch client secret: ').strip()
    #Settings().config['start_time'] = Arguments().start_time
    #Settings().config['video_length'] = Arguments().video_length

    Settings().save()

    Arguments().oauth_token = requests.post(f"https://id.twitch.tv/oauth2/token"
                                            f"?client_id={Settings().config['client_id']}"
                                            f"&client_secret={Settings().config['client_secret']}"
                                            f"&grant_type=client_credentials").json()['access_token']

    # List formats
    if Arguments().print_formats:
        for format_name in [f for f in Settings().config['formats'] if f not in ['all']]:
            format_dictionary = Settings().config['formats'][format_name]
            Logger().log(f'[{format_name}]', retain=False)

            Logger().log('\n', retain=False)
        return

    # Downloader
    if Arguments().video_ids or Arguments().channels:

        if Arguments().video_ids:
            Downloader().videos(Arguments().video_ids)

        if Arguments().channels:
            Downloader().channels(Arguments().channels)

        return

    parser.print_help()

main()

