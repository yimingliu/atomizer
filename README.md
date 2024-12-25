# Atomizer

A prototype Python Atom feed server for transforming arbitrary web pages or JSON API responses into Atom,  RSS 2.0, or iTunes Podcast-compatible RSS 2.0 feeds.

## Get started

- Install server
- Provide an extraction specification file (effectively, a JSON dict of XPath expressions for HTML outputs, or JMESPath expressions for JSON API outputs) on how to transform the target webpage to Atom in `$APPDIR/config/feeds/{feed_name}.json`
  - The name of the spec file will be the shortname of the feed
- Run Flask server using `flask --debug run -p 8000` or `python app.py`
- Navigate to `http://127.0.0.1:8000/feeds/{feed_name}`

## Major prerequisites

- Python 3.9+
- Flask
- feedgen
- parsel

## Example extraction spec file

Check the test cases in tests/ for additional examples of extraction spec files

```
{
  "uri": "https://the-target-website.example.com",
  "entries": "xpath to determine the list of things to extract as posts",
  "title": "....",
  "link": "...",
  "author": "...",
  "author_uri": "...",
  "date": "...",
  "summary": "...",
  "image": "...",
  "USER_AGENT": "Override the default user agent if needed to avoid anti-scraping defenses"
}
```

## Installation

To run locally:

`pip install -r requirements.txt`

`python app.py`

## Deployment

Deploy as WSGI app using preferred WSGI server (e.g. Gunicorn, uWSGI, etc.). See also Flask's documentation about  [deployment](https://flask.palletsprojects.com/en/stable/deploying/).

## TODO
- XSLT + XPath 2 is perhaps a more flexible approach, instead of JSON + XPath 1.0
