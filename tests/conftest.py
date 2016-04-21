from purepage import create_app, couch, db
from couchdb_client import util
import pytest
import logging

logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture(scope="session")
def app():
    app = create_app("purepage.config_test")
    util.load_designs(db, "design")
    yield app
    db.delete()
