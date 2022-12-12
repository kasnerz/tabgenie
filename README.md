# 🧞 TabGenie

Interaction and exploration platform for table-to-text generation datasets.

Work in progress.

## Quickstart
```
pip install -r requirements.txt
flask run
```

## Deployment
```
pip install gunicorn
gunicorn "src:create_app()" -b localhost:8989
```