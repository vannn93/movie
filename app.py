from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

client = MongoClient('mongodb://vania:yusuf123@ac-eg8bint-shard-00-00.jpxaltc.mongodb.net:27017,ac-eg8bint-shard-00-01.jpxaltc.mongodb.net:27017,ac-eg8bint-shard-00-02.jpxaltc.mongodb.net:27017/?ssl=true&replicaSet=atlas-blamiy-shard-0&authSource=admin&appName=Cluster0')
db = client.dbvania
collection = db.bucket_list

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/bucket", methods=["POST"])
def bucket_post():
    bucket_receive = request.form['bucket_give']
    count = db.bucket_list.count_documents({})
    num = count + 1
    doc = {
        'num': num,
        'bucket': bucket_receive,
        'done': 0
    }
    db.bucket_list.insert_one(doc)
    return jsonify({'msg': 'Data berhasil disimpan!'})

@app.route("/bucket/done", methods=["POST"])
def bucket_done():
    num_receive = request.form['num_give']
    db.bucket_list.update_one({'num': int(num_receive)}, {'$set': {'done': 1}})
    return jsonify({'msg': 'Bucket berhasil ditandai selesai!'})

@app.route("/bucket", methods=["GET"])
def bucket_get():
    buckets = list(db.bucket_list.find({}, {'_id': False}))
    return jsonify({'buckets': buckets})

@app.route("/bucket/delete", methods=["POST"])
def bucket_delete():
    num_receive = request.form['num_give']
    db.bucket_list.delete_one({'num': int(num_receive)})
    return jsonify({'msg': 'Bucket deleted successfully!'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
