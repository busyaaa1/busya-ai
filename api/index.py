from flask import Flask, render_template

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

def handler(request, context):
    return app.wsgi_app(request, context)
