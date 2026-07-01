import json
import os
import random
import tempfile

class MarkovChain:
    def __init__(self):
        self.data = {}

    def add(self, item):
        if isinstance(item, list):
            if not item:
                return
            self._add_transition("^", item[0])
            for i in range(len(item) - 1):
                self._add_transition(item[i], item[i+1])
            self._add_transition(item[-1], "$")
        elif isinstance(item, MarkovChain):
            for prefix, suffixes in item.data.items():
                for suffix, count in suffixes.items():
                    self._add_transition(prefix, suffix, count)

    def _add_transition(self, prefix, suffix, count=1):
        if prefix not in self.data:
            self.data[prefix] = {}
        self.data[prefix][suffix] = self.data[prefix].get(suffix, 0) + count

    def remove(self, item):
        if isinstance(item, list):
            if not item:
                return
            self._remove_transition("^", item[0])
            for i in range(len(item) - 1):
                self._remove_transition(item[i], item[i+1])
            self._remove_transition(item[-1], "$")
        elif isinstance(item, MarkovChain):
            for prefix, suffixes in item.data.items():
                for suffix, count in suffixes.items():
                    self._remove_transition(prefix, suffix, count)

    def _remove_transition(self, prefix, suffix, count=1):
        if prefix in self.data and suffix in self.data[prefix]:
            self.data[prefix][suffix] -= count
            if self.data[prefix][suffix] <= 0:
                del self.data[prefix][suffix]
            if not self.data[prefix]:
                del self.data[prefix]

    def generate(self):
        if "^" not in self.data or not self.data["^"]:
            return []

        message = []
        current = "^"
        while True:
            suffixes = self.data.get(current)
            if not suffixes:
                break
            words = list(suffixes.keys())
            weights = list(suffixes.values())
            current = random.choices(words, weights=weights)[0]
            if current == "$":
                break
            message.append(current)
            if len(message) > 200:
                break
        return message

    def write(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(path), delete=False, encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            temp_path = f.name

        os.replace(temp_path, path)

    @classmethod
    def read(cls, path):
        if not os.path.exists(path):
            raise FileNotFoundError()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        chain = cls()
        chain.data = data
        return chain
