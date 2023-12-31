import json

class Constants:
	def __init__(self) -> None:
		with open("config.json", "r") as file:
			for key, value in json.load(file).items(): setattr(self, key.upper(), value)