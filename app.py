from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({'message': 'Hello from Flask!'})

@app.route('/api/data', methods=['POST'])
def post_data():
    data = request.get_json()
    return jsonify({'received': data}), 201

if __name__ == '__main__':
    app.run(debug=True)
