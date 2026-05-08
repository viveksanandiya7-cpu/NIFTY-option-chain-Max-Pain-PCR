import configparser


def load_settings(path="settings.ini"):
    config = configparser.ConfigParser()
    config.read(path)
    return {
        "api_key": config["UPSTOX"]["API_KEY"],
        "api_secret": config["UPSTOX"]["API_SECRET"],
        "access_token": config["UPSTOX"]["ACCESS_TOKEN"],
    }
