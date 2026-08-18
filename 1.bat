cd server
set DMC_BASE_URL=http://192.168.1.14:8000
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
python -m unittest -v
python app.py