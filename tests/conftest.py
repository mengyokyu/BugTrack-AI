import pytest
from app import create_app
from app.extensions import db
@pytest.fixture()
def client(tmp_path):
    app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':f'sqlite:///{tmp_path}/test.db','SECRET_KEY':'test'})
    with app.app_context(): db.drop_all();db.create_all()
    return app.test_client()
