from flask_script import Manager
from purepage import create_app, db
from purepage.util import read_repo, read_articles


app = create_app()
manage = Manager(app)


@manage.command
@manage.option("-u", "--url", dest="url")
def readrepo(url):
    print(read_repo(url, "data"))


@manage.command
@manage.option("-p", "--path", dest="path")
def readarticles(path):
    print(list(read_articles(path)))


@manage.command
def initdb():
    db.load_designs("design")


@manage.command
def savedb():
    db.dump_designs("design")

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    manage.run()
