from flask import Flask, render_template, request, send_file, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
import os

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://:postgres@localhost/postgres'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://mntuzyvzcgjlsu:82272757136c01021ad21469e052f8ad43df98927ccc23c8dccc200447bcc98a@ec2-54-217-250-0.eu-west-1.compute.amazonaws.com:5432/d713cmvmuhr4jd'
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
    file = request.files['inputFile']

    newFile = Music(name=file.filename, media=file.read())
    db.session.add(newFile)
    db.session.commit();

    return 'Saved ' + file.filename + ' to the database!'

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

if __name__ == '__main__':
    app.run(debug=True)