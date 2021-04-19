$env:PY_ENV="development"
pipenv run start
Remove-Item Env:\PY_ENV

pipenv run snakeviz mimic.prof
