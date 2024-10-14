from flask import Flask, request, abort, send_file, url_for
import os, os.path
import io
import re
import json
from lib import atomizer
from urllib.parse import urlparse
import cloudscraper
import socket

# from lib.tw import TWPage

app = Flask(__name__)
# app.config.from_object('config')
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC = os.path.join(APP_ROOT, 'public')
APP_CONFIG = os.path.join(APP_ROOT, 'config')
APP_CONFIG_FEEDS = os.path.join(APP_ROOT, 'config', 'feeds')

app.config['IMAGEPROXY_WHITELIST'] = set()
MAX_PROXY_IMAGE_SIZE = 32 * 1024 * 1024

from werkzeug.utils import secure_filename

if 'SENTRY_DSN' in app.config:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[FlaskIntegration()]
    )

def populate_whitelist():
    # for each *.json file in config_path, load the feed and add the image_proxy_domains to the whitelist
    whitelist = set()
    for file in os.listdir(APP_CONFIG_FEEDS):
        if file.endswith(".json"):
            full_path = os.path.join(APP_CONFIG_FEEDS, file)
            feed = json.load(open(full_path, 'r'))
            if feed.get("image_proxy_domains"):
                domains = set(feed.get("image_proxy_domains"))
                whitelist = whitelist.union(domains)
    return whitelist

app.config['IMAGEPROXY_WHITELIST'] = populate_whitelist()

def load_from_config_file(config_path):
    config = json.load(open(config_path, 'r'))
    feed = atomizer.Page
    # if 'twitter' in config.get('feed_type'):
    #     feed = TWPage
    return feed.load_from_config(config)

def make_feed(feed_id, request):
    feed_id = secure_filename(feed_id)
    feed_config_filepath = os.path.join(APP_CONFIG_FEEDS, feed_id+".json")
    if not os.path.isfile(feed_config_filepath):
        # print(feed_config_filepath)
        abort(404, message="Feed config not found")

    feed = load_from_config_file(feed_config_filepath)
    if feed.config.get("image_proxy_domains"):
        domains = set(feed.config.get("image_proxy_domains"))
        app.config['IMAGEPROXY_WHITELIST'] = app.config['IMAGEPROXY_WHITELIST'].union(domains)
    if not feed:
        abort(400)
    feed.fetch()
    if not feed.entries:
        abort(404, message="No entries found in specified feed")
    # feed_uri = request.url_root
    return feed.to_atom(request.url, image_proxy_uri=url_for('proxy_image', _external=True))

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/feeds/<feed_id>')
def get_atom_feed(feed_id):
    return make_feed(feed_id, request)

def is_allowed_proxy(domain):
    # Ensure domain is in the whitelist
    if domain not in app.config['IMAGEPROXY_WHITELIST']:
        print(f"{domain} Not on whitelist")
        return False

    # Resolve the domain to an IP address and check it's not private
    try:
        ip_address = socket.gethostbyname(domain)
        # Prevent private IP ranges (IPv4)
        if ip_address.startswith(("10.", "192.168.")) or ip_address == "127.0.0.1":
            print(f"banned IP {domain} {ip_address}")
            return False
        # You might also want to check for IPv6 private ranges here
    except socket.gaierror:
        # If domain resolution fails, block the request
        print("can't resolve")
        return False

    return True

@app.route('/imageproxy')
def proxy_image():
    image_url = request.args.get('uri')
    if not image_url:
        abort(400, description="URL parameter is required")
    if not re.match(r'^https?://', image_url):
        abort(400, description="Invalid URL format")

    # Parse the domain from the image URL
    parsed_url = urlparse(image_url)
    domain = parsed_url.netloc

    # Check if the domain is in the whitelist
    if not is_allowed_proxy(domain):
        abort(403, description="Domain not allowed")

    # Fetch the image with the referer header from the url
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    headers = {'Referer': base_url, "User-Agent": request.headers.get("User-Agent")}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(image_url, headers=headers)

    content_length = response.headers.get('Content-Length')
    if content_length and int(content_length) > MAX_PROXY_IMAGE_SIZE:
        abort(413, description="Image size exceeds the maximum allowed limit")

    if response.status_code != 200:
        abort(response.status_code, description=f"Failed to fetch image")

    # Return the image content
    return send_file(io.BytesIO(response.content), mimetype=response.headers['Content-Type'])

if __name__ == '__main__':
    app.run(debug=True)