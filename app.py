from flask import Flask, render_template, request, send_file, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)
DATABASE_URI = 'postgres+psycopg2://mntuzyvzcgjlsu:82272757136c01021ad21469e052f8ad43df98927ccc23c8dccc200447bcc98a@ec2-54-217-250-0.eu-west-1.compute.amazonaws.com:5432/d713cmvmuhr4jd'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://:postgres@localhost/postgres'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
db = SQLAlchemy(app)

class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    media = db.Column(db.LargeBinary)
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
        name = file.filename
        fformat = name[-4:].lower()

        if (fformat == '.mp3') & (len(name) > 4):
            songName = name[:-4]
            newFile = Music(name=songName, media=file.read(), numplays=0, numlikes=0, dislikes=0)
            db.session.add(newFile)
            db.session.commit();

            fileNames += name + ', '

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
    data = Music.query.filter_by(name=name).first()
    file = BytesIO(data.media)
    return Response(stream_with_context(file), mimetype='audio/mp3')

@app.route('/songs')
def songs():
    data = Music.query.all()
    List = ''
    for i in data:
        List += '{0},{1},{2},{3}*'.format(str(i.id), i.name, str(i.numplays), str(i.numlikes))
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
    q = "SELECT id, name, numplays, numlikes, dislikes FROM music"
    df = pd.io.sql.read_sql_query(q, conn)
    df.set_index(['id'], inplace=True)
    df.index.name=None
    return render_template('view.html', tables=[df.to_html()], titles = ['na', 'Dataframe'])

if __name__ == '__main__':
    app.run(debug=True)