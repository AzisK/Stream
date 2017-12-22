from flask import Flask, render_template, request, send_file, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import pandas as pd
from io import BytesIO
import os
from functools import partial
from subprocess import Popen, PIPE

app = Flask(__name__)
DATABASE_URI = 'postgres+psycopg2://mntuzyvzcgjlsu:82272757136c01021ad21469e052f8ad43df98927ccc23c8dccc200447bcc98a@ec2-54-217-250-0.eu-west-1.compute.amazonaws.com:5432/d713cmvmuhr4jd'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://:postgres@localhost/postgres'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = set(['mp3'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS and '..' not in filename

def getAuthor(name):
    return name.split('-')[0]

class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    author = db.Column(db.String(100))
    numplays = db.Column(db.Integer)
    numlikes = db.Column(db.Integer)
    dislikes = db.Column(db.Integer)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('file[]')
    fileNames = ''
    for file in files:
        if allowed_file(file.filename):
            filename = file.filename
            author = getAuthor(filename)
            root = os.path.dirname(os.path.realpath(__file__))
            file.save(os.path.join(root, 'static', 'music', filename))
            fileNames += filename + ', '

            newFile = Music(name=filename, author=author, numplays=0, numlikes=0, dislikes=0)
            db.session.add(newFile)
            db.session.commit();

    if fileNames:
        return 'Saved ' + fileNames[:-2] + ' to the database!'
    else:
        return 'Only .mp3 files are accepted!'

@app.route('/download/<name>')
def download(name):
    data = Music.query.filter_by(name=name).first()
    return send_file(BytesIO(data.media), attachment_filename=data.name, as_attachment=True)

@app.route('/stream/<name>')
def stream(name):
    mp3file = 'static//music//{0}{1}'.format(name, '.mp3')
    process = Popen(['cat', mp3file], stdout=PIPE, bufsize=-1)
    read_chunk = partial(os.read, process.stdout.fileno(), 1024)
    return Response(iter(read_chunk, b''), mimetype='audio/mp3')

@app.route('/delete/<id>')
def delete(id):
    row = Music.query.filter_by(id=id).first()
    os.remove(os.path.join('static', 'music', row.name))
    q = 'DELETE FROM music WHERE id = {}'.format(id)
    db.engine.execute(q)
    return 'Music with id={0} and name={1} deleted'.format(id, row.name)

@app.route('/songs')
def songs():
    data = Music.query.all()
    List = ''
    for i in data:
        List += '{0},{1},{2},{3},{4}*'.format(str(i.id), i.name, i.author, str(i.numplays), str(i.numlikes))
    return List

@app.route('/playadd')
def playAdd():
    id = request.args.get('id')
    q = 'UPDATE music SET numplays = numplays + 1 WHERE id = {}'.format(id)
    db.engine.execute(q)
    return id

@app.route('/likeadd')
def likeAdd():
    id = request.args.get('id')
    q = 'UPDATE music SET numlikes = numlikes + 1 WHERE id = {}'.format(id)
    db.engine.execute(q)
    return id

@app.route('/dislikeadd')
def dislikeAdd():
    id = request.args.get('id')
    q = 'UPDATE music SET dislikes = dislikes + 1 WHERE id = {}'.format(id)
    db.engine.execute(q)
    return id

@app.route('/df')
def df():
    conn = psycopg2.connect("dbname='d713cmvmuhr4jd' user='mntuzyvzcgjlsu' host='ec2-54-217-250-0.eu-west-1.compute.amazonaws.com' password='82272757136c01021ad21469e052f8ad43df98927ccc23c8dccc200447bcc98a'")
    q = "SELECT * FROM music"
    df = pd.io.sql.read_sql_query(q, conn)
    df.set_index(['id'], inplace=True)
    df.index.name=None
    return render_template('view.html', tables=[df.to_html()], titles = ['na', 'Dataframe'])

@app.route('/view')
def view():
    files = ''
    for file in os.listdir('static/music'):
        files += file + ', '
    return files[:-2]

@app.route('/flush')
def flush():
    files = ''
    for file in os.listdir('static/music'):
        os.remove(os.path.join('static', 'music', file))
        files += file + ', '
    return files[:-2] + ' deleted'

if __name__ == '__main__':
    app.run(debug=True)