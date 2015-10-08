# coding:utf-8

from __future__ import unicode_literals
from flask import Flask, Blueprint
from flask import render_template, current_app
from pony.orm import sql_debug, db_session
import logging
import re
import os
from datetime import datetime
from validater import add_validater
from validater.validaters import re_validater

from .extensions import api, db
from . import model
from . import article
from . import githooks
from . import user
from . import view
from . import bloguser

__all__ = ["create_app", "api", "db"]


def create_app():
    app = Flask(__name__)
    app.config.from_object('kkblog.config.default_config')
    if 'KKBLOG_CONFIG' in os.environ:
        app.config.from_envvar('KKBLOG_CONFIG')
    app.config["ARTICLE_DEST"] = os.path.join(app.root_path, app.config["ARTICLE_DEST"])
    if app.config["DEBUG"]:
        sql_debug(True)

    # create data dir
    dir_data = os.path.join(app.root_path, "data")
    if not os.path.exists(dir_data):
        os.makedirs(dir_data)
    bp_api = Blueprint('api', __name__, static_folder='static')
    api_config = {
        "bootstrap": "/static/lib/bootstrap.css",
        "permission_path": "config/permission.json",
        "auth_secret": "auth_secret",
    }
    api.init_app(bp_api, **api_config)

    config_validater(app)
    config_view(app)
    config_api(app)
    config_db(app)
    config_error_handler(app)
    config_before_handler(app)

    app.register_blueprint(bp_api, url_prefix='/api')
    return app


def config_validater(app):

    def plus_int_validater(v):
        try:
            i = int(v)
            return (i > 0, i)
        except:
            pass
        return (False, None)

    def friendly_date(date):
        s = "{}年{}月{}日".format(date.year, date.month, date.day)
        return s

    def iso_datetime_validater(v):
        if isinstance(v, datetime):
            return (True, v.isoformat())
        else:
            return (False, None)

    def friendly_date_validater(v):
        if isinstance(v, datetime):
            return (True, friendly_date(v))
        else:
            return (False, None)
    re_password = re.compile(ur"""^[a-zA-Z0-9~!@#$%^&*(),./;'<>?:"-_=+]{6,16}$""")
    add_validater("+int", plus_int_validater)
    add_validater("password", re_validater(re_password))
    add_validater("iso_datetime", iso_datetime_validater)
    add_validater("friendly_date", friendly_date_validater)

    user_roles = ["user.admin", "user.normal"]

    def userrole_validater(v):
        return (True, v) if v in user_roles else (False, None)
    add_validater("userrole", userrole_validater)

    bloguser_roles = ["bloguser.admin", "bloguser.normal"]

    def bloguser_role_validater(v):
        return (True, v) if v in bloguser_roles else (False, None)
    add_validater("bloguser_role", bloguser_role_validater)


def config_view(app):
    view_urls = (
        (view.index, '/'),
        (view.page_article, '/article/<name>'),
    )
    for v, url in view_urls:
        app.route(url)(v)


def config_api(app):
    reslist = [
        article.Article,
        article.Tag,
        githooks.GitHooks,
        user.User,
        bloguser.BlogUser,
    ]
    for res in reslist:
        api.add_resource(res)


def config_error_handler(app):

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404


def config_db(app):
    db.bind(app.config["DATABASE_NAME"],
            app.config["DATABASE_PATH"],
            create_db=True)
    db.generate_mapping(create_tables=True)


def config_before_handler(app):

    @app.before_first_request
    def init():
        api.gen_resjs()
        api.gen_resdocs()
        email = current_app.config["USER_ADMIN_EMAIL"]
        password = current_app.config["USER_ADMIN_PASSWORD"]
        repo = current_app.config["USER_ADMIN_REPO_URL"]
        user.add_admin(email, password)
        with db_session:
            u = model.User.get(username=email)
            bloguser.add_admin(u.id, repo)
