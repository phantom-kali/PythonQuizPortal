from flask import Flask, jsonify, render_template, request, redirect, session, flash
import os
import json
from datetime import datetime
import re

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

        # Extract function name from response
        match = re.search(r'def\s+(\w+)\(', response)
        if match:
            function_name = match.group(1)
            print(function_name)
        else:
            return jsonify({'success': False, 'message': 'Function definition not found in response'}), 400

        exec(response)  

        test_cases = load_test_cases() 
        for testcase in test_cases:
            if testcase['title'] == question_title:
                input_data = testcase['input']
                expected_output = testcase['expected_output']

                # Execute the function with input data
                output = function_name(input_data)

                if output == expected_output:
                    return jsonify({'success': True}), 200
                else:
                    return jsonify({'success': False, 'message': 'Test failed'}), 200

        return jsonify({'success': False, 'message': 'Question title not found'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


def load_test_cases():
    with open('test_cases.json') as f:
        return json.load(f)


@app.route('/submit_response', methods=['POST'])
def submit_response():
    username = session.get('username')
    if not username:
        flash("Unauthorized access", "error")
        return redirect('/')

    response = request.form['response']
    if not response:
        return "empty"

    # Sanitize and validate input, skipping this to maintain code structure
    sanitized_response = response

    if not os.path.exists('responses'):
        os.makedirs('responses')

    filename = f"responses/{username}.txt"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(filename, 'a') as f:
        f.write(f"{sanitized_response}\nSubmitted on: {timestamp}\n\n")

    return redirect('/finished')

@app.route('/finished')
def finished():
    return render_template('finished.html')

def check_existing_user(username):
    return os.path.exists(f'responses/{username}.txt')

if __name__ == '__main__':
    app.run(debug=True)
