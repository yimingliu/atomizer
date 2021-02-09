# Atomizer

A prototype Python Atom feed server for transforming arbitrary web pages into Atom Feeds

## Get started

- Install server
- Provide a JSON specification file (effectively, a dict of XPath expressions) on how to transform the target webpage to Atom in `$APPDIR/config/feeds/{feed_name}.json`
- Navigate to `http://127.0.0.1:5000/feeds/{feed_name}`

## Major prerequisites

- Flask
- feedgen
- parsel

## Example JSON spec file

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

## TODO
- XSLT + XPath 2 is perhaps a more flexible approach, instead of JSON + XPath 1.0
