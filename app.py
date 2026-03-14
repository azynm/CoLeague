#Main entry point for frontend 
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<h1>Hello, World!</h1><p>My Flask app is alive.</p>"

if __name__ == "__main__":
    app.run(debug=True)