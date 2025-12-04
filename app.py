from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list')
def list_page():
    return render_template('list.html')

@app.route('/feed')
def feed():
    return render_template('feed.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login')
def login():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
