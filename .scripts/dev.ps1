$env:PY_ENV="development"

nodemon --watch main.py --watch mimic --ext py --exec python main.py

Remove-Item Env:\PY_ENV
