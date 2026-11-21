# AcronyBot

A Discord bot that spots acronyms in server messages and replies with probable expansions. Optional reactions let readers rate the guesses.

![AcronyBot cover](.github/images/readme-hero.svg)

## Table of Contents

- [Setup](#setup)
- [Technologies](#technologies)

## Setup

Run from the repository root. Review `requirements.txt`, install the Python dependencies including PyYAML, add the bot token to your local `config.yml`, then run `python bot.py`. Never commit a live token. This client has not been verified against current Discord APIs.

## Technologies

- [Python](https://www.python.org/)
- [discord.py](https://discordpy.readthedocs.io/)
- [PyYAML](https://pyyaml.org/)
