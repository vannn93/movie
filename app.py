from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import requests
import re

OMDB_API_KEY = "d9368fe7"

mongodb_uri = "mongodb+srv://vania:yusuf123@ac-eg8bint-shard-00-00.jpxaltc.mongodb.net/?ssl=true&replicaSet=atlas-blamiy-shard-0&authSource=admin&appName=Cluster0"

client = MongoClient(mongodb_uri, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
db = client.dbvania
collection = db.movies

app = Flask(__name__)

def get_movie_info(url):
    match = re.search(r'tt\d+', url)
    if not match:
        return None, "URL tidak valid"
    imdb_id = match.group()
    try:
        api_url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"
        response = requests.get(api_url, timeout=10)
        data = response.json()
        if data.get('Response') == 'True':
            return {
                'title': data.get('Title', 'Unknown'),
                'image': data.get('Poster', ''),
                'description': data.get('Plot', 'No description')
            }, None
        return None, data.get('Error', 'Film tidak ditemukan')
    except Exception as e:
        return None, str(e)

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/movie", methods=["POST"])
def movie_post():
    url_receive = request.form['url_give']
    star_receive = request.form['star_give']
    comment_receive = request.form['comment_give']
    
    try:
        star = float(star_receive)
        if star < 1 or star > 5:
            return jsonify({'msg': 'Rating 1-5'}), 400
    except:
        return jsonify({'msg': 'Rating tidak valid'}), 400
    
    movie_info, error = get_movie_info(url_receive)
    if error:
        return jsonify({'msg': error}), 400
    
    doc = {
        'image': movie_info['image'] if movie_info['image'] != 'N/A' else '',
        'title': movie_info['title'],
        'description': movie_info['description'],
        'star': star_receive,
        'comment': comment_receive,
        'url': url_receive
    }
    collection.insert_one(doc)
    return jsonify({'msg': f'✅ {movie_info["title"]} berhasil disimpan!'})

@app.route("/movie", methods=["GET"])
def movie_get():
    movies = list(collection.find({}, {'_id': False}))
    return jsonify({'movies': movies})

@app.route("/delete_all", methods=["POST"])
def delete_all():
    result = collection.delete_many({})
    return jsonify({'msg': f'Menghapus {result.deleted_count} data'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import requests
import re

OMDB_API_KEY = "d9368fe7"

mongodb_uri = "mongodb+srv://vania:yusuf123@ac-eg8bint-shard-00-00.jpxaltc.mongodb.net/?ssl=true&replicaSet=atlas-blamiy-shard-0&authSource=admin&appName=Cluster0"

client = MongoClient(mongodb_uri, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
db = client.dbvania
collection = db.movies

app = Flask(__name__)

def get_movie_info(url):
    """Ambil info film dari OMDB API"""
    match = re.search(r'tt\d+', url)
    
    if not match:
        return None, "URL tidak valid. Harus mengandung ID IMDb seperti tt0111161"
    
    imdb_id = match.group()
    
    try:
        api_url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}&plot=full"
        response = requests.get(api_url, timeout=10)
        data = response.json()
        
        if data.get('Response') == 'True':
            movie_data = {
                'title': data.get('Title', 'Unknown'),
                'image': data.get('Poster', ''),
                'description': data.get('Plot', 'No description')
            }
            return movie_data, None
        else:
            return None, data.get('Error', 'Film tidak ditemukan')
            
    except Exception as e:
        return None, f"Error koneksi: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/movie", methods=["POST"])
def movie_post():
    url_receive = request.form['url_give']
    star_receive = request.form['star_give']
    comment_receive = request.form['comment_give']
    
    try:
        star = float(star_receive)
        if star < 1 or star > 5:
            return jsonify({'msg': 'Rating harus antara 1-5'}), 400
    except:
        return jsonify({'msg': 'Rating tidak valid'}), 400
    
    movie_info, error = get_movie_info(url_receive)
    
    if error:
        return jsonify({'msg': f'Gagal mengambil data film: {error}'}), 400
    
    doc = {
        'image': movie_info['image'] if movie_info['image'] != 'N/A' else '',
        'title': movie_info['title'],
        'description': movie_info['description'] if movie_info['description'] != 'N/A' else 'Tidak ada deskripsi',
        'star': star_receive,
        'comment': comment_receive,
        'url': url_receive
    }
    
    try:
        collection.insert_one(doc)
        return jsonify({'msg': f'✅ {movie_info["title"]} berhasil disimpan!'})
    except Exception as e:
        return jsonify({'msg': f'Gagal menyimpan: {str(e)}'}), 500

@app.route("/movie", methods=["GET"])
def movie_get():
    try:
        movies = list(collection.find({}, {'_id': False}))
        valid_movies = [m for m in movies if m.get('title') and m.get('title') != 'Movie Not Found']
        return jsonify({'movies': valid_movies})
    except Exception as e:
        return jsonify({'movies': [], 'msg': str(e)}), 500

@app.route("/delete_all", methods=["POST"])
def delete_all():
    result = collection.delete_many({})
    return jsonify({'msg': f'Menghapus {result.deleted_count} data'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
