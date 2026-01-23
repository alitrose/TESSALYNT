import os
from flask import Flask, render_template_string, request
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here"))
app = Flask(__name__)
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Notes Generator </title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background: #121212; 
            color: #f1f1f1;
        }
        h1 { color: #00adb5; }
        form { margin-bottom: 20px; }
        input { 
            padding: 10px; 
            margin: 5px; 
            width: 300px; 
            background: #1e1e1e; 
            color: #f1f1f1; 
            border: 1px solid #333; 
            border-radius: 5px;
        }
        button { 
            padding: 10px 20px; 
            background: #00adb5; 
            color: white; 
            border: none; 
            border-radius: 5px;
            cursor: pointer; 
        }
        button:hover { background: #007d82; }
        .notes { 
            background: #1e1e1e; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 0 10px rgba(0,0,0,0.5); 
            margin-top: 20px; 
            color: #e0e0e0;
        }
        pre { white-space: pre-wrap; font-family: Consolas, monospace; }
    </style>
</head>
<body>
    <h1> AI Notes Generator</h1>
    <form method="POST">
        <input type="text" name="stream" placeholder="Stream (e.g., B.Tech, B.Sc)" required><br>
        <input type="text" name="subject" placeholder="Subject" required><br>
        <input type="text" name="topic" placeholder="Topic" required><br>
        <button type="submit">Generate Notes</button>
    </form>

    {% if notes %}
    <div class="notes">
        <h2>Generated Notes</h2>
        <pre>{{ notes }}</pre>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    notes = ""
    if request.method == "POST":
        stream = request.form["stream"]
        subject = request.form["subject"]
        topic = request.form["topic"]
        prompt = f"Generate clear, structured study notes for {stream} students on the subject {subject}, topic: {topic}."
        model = genai.GenerativeModel("gemimi-pro")
        response = model.generate_content(prompt)
        notes = response.text
    return render_template_string(HTML_PAGE, notes=notes)
if __name__ == "__main__":
    app.run(debug=True)