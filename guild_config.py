import json
import os

DEFAULT_CONFIG = {
    "log_channel_id": None,
    "punishment": "delete",
}


class GuildConfig:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self):
        if os.path.isfile(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    self._data = json.load(f)
            except Exception as e:
                print(f"Failed to load guild config: {e}")
                self._data = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, guild_id: int) -> dict:
        gid = str(guild_id)
        if gid not in self._data:
            self._data[gid] = dict(DEFAULT_CONFIG)
            self._save()
        return self._data[gid]

    def set(self, guild_id: int, key: str, value):
        gid = str(guild_id)
        if gid not in self._data:
            self._data[gid] = dict(DEFAULT_CONFIG)
        self._data[gid][key] = value
        self._save()

    def remove(self, guild_id: int):
        gid = str(guild_id)
        self._data.pop(gid, None)
        self._save()

    def is_setup(self, guild_id: int) -> bool:
        cfg = self.get(guild_id)
        return cfg["log_channel_id"] is not None
