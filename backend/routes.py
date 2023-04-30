from . import app
import os
import json
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200


@app.route('/song', methods=['GET'])
def songs():
    #db = client.songs
    ssongs = db.songs.find()
    song_list = parse_json(ssongs)
    
    return jsonify({'songs': song_list}), 200
    



@app.route('/song/<int:id>', methods=['GET'])
def get_song_by_id(id):
    song = parse_json( db.songs.find_one({"id": id}) )
    if song is None:
        return jsonify({"message": "song with id not found"}), 404
    else:
        return jsonify(song), 200


@app.route('/song', methods=['POST'])
def create_song():
    # Extract song data from request body
    song = request.get_json()
    id = song['id']

    # Check if song with id already exists
    if db.songs.find_one({"id": id}):
        return {"message": f"song with id {id} already present"}, 302

    # Append song to database
    song["id"] = id
    db.songs.insert_one(song)

    # Return success message
    return {"message": "song created successfully"}, 200


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):

    # get data from the json body
    song_in = request.json

    song = db.songs.find_one({"id": id})

    if song == None:
        return {"message": "song not found"}, 404

    updated_data = {"$set": song_in}

    result = db.songs.update_one({"id": id}, updated_data)

    if result.modified_count == 0:
        return {"message": "song found, but nothing updated"}, 200
    else:
        return parse_json(db.songs.find_one({"id": id})), 201


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):

    result = db.songs.delete_one({"id": id})
    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    else:
        return "", 204
