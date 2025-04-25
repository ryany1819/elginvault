import psycopg2
import configparser
from dotenv import load_dotenv, find_dotenv
import os

# Ensure the .env file is loaded only once
load_dotenv(find_dotenv(), override=False)


def get_db_params():
    # Read config.ini
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '../config.ini')
    config.read(config_path)
    db_params = dict(config['database'])

    # Override config values with environment variables if they exist
    for key in ['host', 'port', 'dbname', 'user', 'password']:
        env_value = os.getenv(f'DB_{key.upper()}')
        if env_value:
            db_params[key] = env_value

    return db_params


def get_db_connection():
    params = get_db_params()
    try:
        connection = psycopg2.connect(**params)
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None


def close_db_connection(connection):
    if connection:
        connection.close()
        print("Database connection closed.")
    else:
        print("No connection to close.")
