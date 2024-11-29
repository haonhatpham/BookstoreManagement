from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
import cloudinary
from flask_login import LoginManager
import json

app = Flask(__name__)
app.secret_key = 'HJGGHD*^&R$YGFGHDYTRER&*TRTYCHG^R&^T'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/bookstore3hdb?charset=utf8mb4" % quote("1234")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 12


db = SQLAlchemy(app)

cloudinary.config(cloud_name='dtcxjo4ns',
                  api_key="172464483393764",
                  api_secret="1yivw8eviVI7BBQ7q9S909OS2mU")



