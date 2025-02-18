import os
import pymysql
pymysql.install_as_MySQLdb()

class Config:
    SECRET_KEY='a3f5b8d2e6c7a9d9e1b2c4f5e6d7a9b8c2d4e6f7a9b1c3d4e5f6a7d8b9c2e3f'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/library_management'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
