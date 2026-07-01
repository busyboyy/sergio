import yaml

class Config:
    def __init__(self):
        self.telegram_bot_token = ""

    @classmethod
    def read(cls, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        config = cls()
        config.telegram_bot_token = data.get('telegram_bot_token')
        return config