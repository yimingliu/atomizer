from flask import Flask, request, abort
import os.path
import atomizer

app = Flask(__name__)
# app.config.from_object('config')
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC = os.path.join(APP_ROOT, 'public')
APP_CONFIG = os.path.join(APP_ROOT, 'config')
APP_CONFIG_FEEDS = os.path.join(APP_ROOT, 'config', 'feeds')

from werkzeug.utils import secure_filename
from feedgen.feed import FeedGenerator

if 'SENTRY_DSN' in app.config:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[FlaskIntegration()]
    )


def make_feed(feed_id, request):
    feed_id = secure_filename(feed_id)
    feed_config_filepath = os.path.join(APP_CONFIG_FEEDS, feed_id+".json")
    if not os.path.isfile(feed_config_filepath):
        # print(feed_config_filepath)
        abort(404)
    feed = atomizer.Page.load_from_config_file(feed_config_filepath)
    if not feed:
        abort(400)
    feed.fetch()
    # feed_uri = request.url_root
    return feed.to_atom(request.url)


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/feeds/<feed_id>')
def get_atom_feed(feed_id):
    return make_feed(feed_id, request)

if __name__ == '__main__':
    app.run(debug=True)