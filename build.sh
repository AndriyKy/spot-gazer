#!/bin/bash

# Set up a main virtual environment
sudo apt install -y screen
export PYTHONPATH="$(pwd)"
python3 -m venv .venv
source .venv/bin/activate
echo
echo "[INFO] Installing main dependencies into a '$VIRTUAL_ENV' ..."
pip3 install -r requirements.txt

pre-commit install

echo
echo "[INFO] Performing migrations."
python3 manage.py migrate

echo
echo "[INFO] Run tests."
python3 -Wa manage.py test tests
