from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

ANIMATION_FILE = "hologram-animation.json"

def compute_delta(initial_frame, current_frame):
    delta = []
    for index, (initial_color, current_color) in enumerate(zip(initial_frame, current_frame)):
        if initial_color != current_color:
            delta.append({"index": index, "color": current_color})
    return delta

@app.route('/save', methods=['POST'])
def save_data():
    try:
        data = request.json
        current_pixels = data.get('pixels', [])

        if not current_pixels:
            return jsonify({"error": "No pixel data received"}), 400

        # Check if animation file exists
        if not os.path.exists(ANIMATION_FILE):
            # Save initial frame
            animation = [current_pixels]
            with open(ANIMATION_FILE, "w") as f:
                json.dump(animation, f, indent=4)
            return jsonify({"message": "Initial frame saved successfully"}), 200
        else:
            # Load animation data and get initial frame
            with open(ANIMATION_FILE, "r") as f:
                animation = json.load(f)
            initial_frame = animation[0]

            # Compute delta from initial frame
            delta = compute_delta(initial_frame, current_pixels)

            # Append delta to animation
            animation.append(delta)
            with open(ANIMATION_FILE, "w") as f:
                json.dump(animation, f, indent=4)

            return jsonify({"message": "Delta frame saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)