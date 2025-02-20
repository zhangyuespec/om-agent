from flask import Flask, request, jsonify, render_template, Response
from ops_agent import OpsAgent
import json
import logging
from logging.handlers import RotatingFileHandler
import yaml

# 加载配置文件
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

app = Flask(__name__)

# Configure logging
handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Initialize the agent
agent = OpsAgent(
    wiki_domain=config["wiki"]["domain"],
    wiki_username=config["wiki"]["username"],
    wiki_password=config["wiki"]["password"],
    persist_directory=config["vector_db"]["persist_directory"]
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init', methods=['POST'])
def init():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    
    data = request.get_json()
    page_id = data.get('page_id')
    if not page_id:
        return jsonify({"error": "Missing 'page_id' in request"}), 400
    
    try:
        agent.initialize(page_id)
        return jsonify({"message": "Vector database initialized successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['GET'])
def query():
    question = request.args.get('question')
    if not question:
        return jsonify({"error": "Missing 'question' parameter"}), 400
    
    try:
        return Response(
            agent.stream_query(question),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host=config["app"]["host"], port=config["app"]["port"], debug=config["app"]["debug"]) 