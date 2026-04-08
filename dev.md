## venv
> powershell
```shell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r ./requirements.txt
cd src
uvicorn main:app --host 0.0.0.0 --port 51205 --reload
```

## uv
> powershell
```shell
uv venv
uv pip install -r ./requirements.txt
cd src
python run main.py
```