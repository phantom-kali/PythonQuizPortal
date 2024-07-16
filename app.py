from flask import Flask, jsonify, render_template, request, redirect, session, flash
import os
import json
from datetime import datetime
import re
import random
import ast
import time
from functools import wraps
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = 'your_secret_key'
# csrf = CSRFProtect(app)

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

        if check_existing_user(sanitized_username):
            flash("Username already exists. Choose a different username.", "error")
            return redirect('/')

        session['username'] = sanitized_username

        with open('questions.json', 'r') as f:
            questions = json.load(f)
        return render_template('questions.html', questions=questions)
    else:
        return redirect('/')
    

@app.route('/test_code', methods=["POST"])
def test_cases():
    try:
        response = request.form['response']
        question_title = request.form.get('question_title')

        if not response or not question_title:
            return jsonify({'success': False, 'message': 'Missing data in request'}), 400
        
        # Parse the function
        tree = ast.parse(response)
        function_def = tree.body[0]
        if not isinstance(function_def, ast.FunctionDef):
            return jsonify({'success': False, 'message': 'Invalid function definition'}), 400

        function_name = function_def.name

        # Create a restricted global environment
        safe_globals = {
            '__builtins__': {
                'range': range,
                'len': len,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'sum': sum,
                'min': min,
                'max': max,
                'random': random,
                'print': print
            }
        }

        exec(response, safe_globals)

        user_function = safe_globals[function_name]

        test_cases = load_test_cases()
        for testcase in test_cases:
            if testcase['title'] == question_title:
                input_data = ast.literal_eval(testcase['input'])
                expected_output = ast.literal_eval(testcase['expected_output'])

                output = user_function(input_data)

                if output == expected_output:
                    return jsonify({'success': True}), 200
                else:
                    return jsonify({'success': False, 'message': 'Test failed. Expected {} but got {}'.format(expected_output, output)}), 200

        return jsonify({'success': False, 'message': 'Question title not found'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

def load_test_cases():
    with open('test_cases.json') as f:
        return json.load(f)

# Rate limiting
def rate_limit(limit=10, per=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not hasattr(wrapped, 'last_request'):
                wrapped.last_request = {}
            now = time.time()
            ip = request.remote_addr
            if ip in wrapped.last_request:
                if now - wrapped.last_request[ip] < per / limit:
                    return jsonify({'error': 'Rate limit exceeded'}), 429
            wrapped.last_request[ip] = now
            return f(*args, **kwargs)
        return wrapped
    return decorator

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/submit_response', methods=['POST'])
@rate_limit(limit=5, per=60)  # 5 requests per minute
def submit_response():
    username = session.get('username')
    if not username:
        flash("Unauthorized access", "error")
        return redirect('/')
    
    response = request.form['response']
    if not response:
        return "empty"
    
    sanitized_response = response  # TODO: sanitize while maintaing identation
    
    if not os.path.exists('responses'):
        os.makedirs('responses')
    
    filename = secure_filename(f"{username}.txt")
    filepath = os.path.join('responses', filename)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(filepath, 'a') as f:
        f.write(f"{sanitized_response}\nSubmitted on: {timestamp}\n\n")
    
    return redirect('/finished')

@app.route('/finished')
def finished():
    return render_template('finished.html')

def check_existing_user(username):
    return os.path.exists(f'responses/{username}.txt')

if __name__ == '__main__':
    app.run(debug=True)
