from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/questions', methods=['GET', 'POST'])
def questions():
    if request.method == 'POST':
        username = request.form['username']
        if username:
            sanitized_username = ''.join([char for char in username if char.isalnum()])
        if not username or not sanitized_username:
            flash("Invalid username", "error")
            return redirect('/')

        session['username'] = sanitized_username

        with open('questions.json', 'r') as f:
            questions = json.load(f)
        return render_template('questions.html', questions=questions)
    else:
        return redirect('/')

@app.route('/submit_response', methods=['POST'])
def submit_response():
    username = session.get('username')
    if not username:
        flash("Unauthorized access", "error")
        return redirect('/')

    response = request.form['response']
    if not response:
        return "empty"

    # Sanitize and validate input. Leaving it as it is to maintain code format
    sanitized_response = response

    # Ensure the responses directory exists
    if not os.path.exists('responses'):
        os.makedirs('responses')

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{username}_{timestamp}.txt"
    with open(f'responses/{filename}', 'a') as f:
        f.write(sanitized_response + '\n')
        f.write(f"Submitted on: {timestamp}\n\n")

    return "success"

@app.route('/finished')
def finished():
    return render_template('finished.html')

if __name__ == '__main__':
    app.run()
