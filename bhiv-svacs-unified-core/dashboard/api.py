from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route("/api/dashboard")
def dashboard():

    with open(
        "storage/dashboard/dashboard_runtime.json"
    ) as f:

        data = json.load(f)

    return jsonify(data)

@app.route("/api/runtime")
def runtime():

    with open(
        "storage/runtime/single_trace_runtime.json"
    ) as f:

        data = json.load(f)

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)