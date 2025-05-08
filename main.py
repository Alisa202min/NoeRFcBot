from flask import Flask, render_template, request, redirect, url_for, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Radio Frequency and Telecommunications Equipment Store - API Server"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)