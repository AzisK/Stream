from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:postgres@localhost/postgres'
db = SQLAlchemy(app)

class Music(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	media = db.Column(db.LargeBinary)

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

@app.route('/download/<id>')
def download(id):
	file_data = Music.query.filter_by(id=id).first()
	return send_file(BytesIO(file_data.media), attachment_filename=file_data.name, as_attachment=True)
		
if __name__ == '__main__':
	app.run(debug=True)