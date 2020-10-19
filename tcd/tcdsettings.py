import json
import pathlib
from typing import Optional, Dict, Any

from logger import Logger, Log
from singleton import Singleton


class Settings(metaclass=Singleton):

    def __init__(self, filepath: Optional[str] = None, reference_filepath: Optional[str] = None):
        """
        Initialize settings with filepath and reference filepath
        :param filepath: Path to settings file
        :param reference_filepath: Path to reference settings file
        """
        filepath = "settings.json"
        if filepath is None:
            print('Settings filepath was not provided')
            exit(1)

        self.filepath = pathlib.Path(filepath)
        self.directory: pathlib.Path = self.filepath.parent

        self.reference_filepath = pathlib.Path(reference_filepath)

        self.config: Dict[str, Any] = self.load(filepath)

        # commented out update as settings config file is hard coded
        '''
        if self.out_of_date():
            self.update()
            Logger().log('Updated to version {}'.format(self.config.get('version')))
        '''

    def load(self, filepath: str) -> Dict[str, Any]:
        """
        Load dictionary from json file
        :param filepath: filepath to load from
        :return: Configuration dictionary
        """

        # Create settings file from reference file if necessary
        if not self.filepath.exists():
            self.directory.mkdir(parents=True, exist_ok=True)

            # Missing reference file
            if not self.reference_filepath.exists():
                Logger().log(f'Could not find {self.reference_filepath}', Log.CRITICAL)
                exit(1)

            # Load config from reference settings
            with open(self.reference_filepath, 'r') as file:
                config = json.load(file)

            Settings.write(self.filepath, data=config)

            return config

        # Load from settings file
        try:
            with open(filepath, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print('Invalid settings format')
            exit(1)

    @staticmethod
    def write(filepath: str, data: dict) -> None:
        """
        Save configuration to settings file
        :param filepath: Filepath to save to
        :param data: Configuration dictionary to save
        :return: None
        """
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)

    def save(self) -> None:
        """
        Save settings to file
        :return: None
        """
        Settings.write(self.filepath, self.config)

    def out_of_date(self) -> bool:
        reference: dict = self.load(self.reference_filepath)

        return self.config.get('version') != reference.get('version')

    def update(self) -> None:
        """
        Update configuration settings and file using reference settings.
        :return: None
        """
        backup_path = pathlib.Path('{}/settings.{}.backup.json'.format(self.directory, self.config['version']))

        Settings.write(backup_path, self.config)

        new_config: dict = self.load(self.reference_filepath)

        Logger().log(f'Updating settings file to v{new_config["version"]}')

        # Copy client ID to new config file
        Logger().log('Transferring client id and secret', Log.VERBOSE)
        new_config['client_id'] = self.config.get('client_id', None)
        new_config['client_secret'] = self.config.get('client_secret', None)

        # Copy user-defined formats to new config file
        for format_name, format_dictionary in dict(self.config['formats']).items():
            if format_name not in new_config['formats']:
                new_config['formats'][format_name] = format_dictionary
                Logger().log(f'Transferring format: {format_name}', Log.VERBOSE)

        Logger().log(f'Previous settings have been backed up to {backup_path}')

        # Overwrite current config with new
        Settings.write(self.filepath, new_config)
        self.config = new_config
