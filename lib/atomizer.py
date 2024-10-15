import requests
import parsel
import datetime
import dateutil.parser
from feedgen.feed import FeedGenerator
import cloudscraper
from urllib.parse import urlparse

class Entry(object):
    """
    Represents an individual entry in a feed
    """
    def __init__(self, link, title, date, author="", author_uri="", summary=None, image=None, enclosures=None):
        self.link = link
        self.date = date
        self.title = title
        self.summary = summary
        self.image = [x for x in image if x and x != ""]
        self.author = author
        self.enclosures = enclosures
        self.author_uri = author_uri

    def __repr__(self):
        return self.__dict__.__repr__()

    @property
    def summary_html(self):
        return "<br>".join(self.summary)

    @property
    def image_html(self):
        return self.generate_image_html()

    def generate_image_html(self, image_proxies=None):
        """
        Given a list of image URLs, return a string of HTML img tags for inclusion in a content block
        Optionally, pass a dict of domain: proxy_uri to proxy the images so they can be displayed in the feed.
        This is largely to avoid hotlinking issues with images.
        :param image_proxies: dict of domain: proxy_uri
        :return: str
        """
        images = self.image
        if not images:
            return ""
        if image_proxies:
            # if we have image proxies specified, check the domain of each image
            images = []
            for image in self.image:
                parsed = urlparse(image)
                if parsed.netloc in image_proxies:
                    images.append(image_proxies[parsed.netloc] + f"?uri={image}")
                else:
                    images.append(image)
        image_tags = "\n".join(["<img src='%s' />" % x for x in images])
        return f"<div class='post_image'>{image_tags}</div>"

    @property
    def content_html(self):
        return f"<div class='post_text'>{self.summary_html}</div>"


class Page(object):

    def __init__(self, config):
        self.entries = []
        self.config = config
        self.uri = self.config['uri']
        self.title = self.uri

    @property
    def canonical_uri(self):
        return self.uri if not self.is_list_like(self.uri) else self.uri[0]

    @classmethod
    def load_from_config(cls, config_dict):
        return cls(config_dict)

    @staticmethod
    def is_list_like(obj):
        return isinstance(obj, list) or isinstance(obj, tuple)

    def fetch(self):
        entries = []
        multi_uris = self.is_list_like(self.uri)
        uris = self.uri if multi_uris else [self.uri]
        for uri in uris:
            entries.extend(self.fetch_uri(uri))
        if entries and multi_uris:
            entries.sort(key=lambda x: x.date, reverse=True)
        self.entries = entries
        return self.entries

    def fetch_uri(self, uri):
        headers = self.config.get('headers', {})
        entries = []
        if self.config.get('USER_AGENT') and 'User-Agent' not in headers:
            headers['User-Agent'] = self.config.get('USER_AGENT')
        if self.config.get("handling") == "cloudflare":
            response = self.get_cloudflare(uri, headers=headers)
        else:
            response = requests.get(uri, headers=headers, timeout=120)
        if response.status_code < 300:
            entries = self.parse_entries_from_html(response.text)
        return entries

    @staticmethod
    def get_cloudflare(uri, **kwargs):
        scraper = cloudscraper.create_scraper()
        try:
            response = scraper.get(uri, **kwargs)
        except Exception as e:
            print("Error fetching %s: %s" % (uri, e))
            return None
        return response

    def parse_entries_from_html(self, html):
        parsed_entries = []
        selector = parsel.Selector(html)
        entries = selector.xpath(self.config['entries'])
        self.title = selector.xpath("//head/title/text()").get() or self.title
        if entries:
            for entry in entries:
                link = entry.xpath(self.config['link']).get()
                if not link:
                    continue
                date = entry.xpath(self.config['date']).get() if self.config.get('date') else None
                item = Entry(link=link,
                             author=entry.xpath(self.config['author']).get() if self.config.get('author') else "",
                             author_uri=entry.xpath(self.config['author_uri']).get() if self.config.get(
                                 'author_uri') else "",
                             title=entry.xpath(self.config['title']).get() if self.config.get('title') else link,
                             date=dateutil.parser.parse(date) if date else datetime.datetime.now(datetime.timezone.utc),
                             summary=entry.xpath(self.config['summary']).getall() if self.config.get('summary') else [],
                             image=entry.xpath(self.config['image']).getall() if self.config.get('image') else []
                             )
                parsed_entries.append(item)
        if parsed_entries:
            parsed_entries.sort(key=lambda x: x.date, reverse=True)
        return parsed_entries

    @staticmethod
    def ensure_tz_utc(dt):
        """
        Given a datetime object, return converted UTC time if it already has a timezone.  Otherwise assume
        it's a UTC time to begin with and attach a timezone to the object before returning it
        """
        if not dt:
            return None
        if dt.tzinfo:
            if dt.tzinfo != datetime.timezone.utc:
                return dt.astimezone(datetime.timezone.utc)
            else:
                return dt
        else:
            return dt.replace(tzinfo=datetime.timezone.utc)

    def to_atom(self, deployment_uri, use_summary=False, image_proxy_uri=None):
        fg = FeedGenerator()
        fg.load_extension('podcast')
        fg.id(deployment_uri)
        fg.title(self.title)
        fg.author({"name": "Atomizer/1.0"})
        fg.generator("Atomizer")
        fg.link(href=self.canonical_uri, rel='alternate', type="text/html")
        fg.link(href=deployment_uri, rel='self')
        fg.description(self.title)

        for entry in self.entries:

            feed_item = fg.add_entry(order='append')
            feed_item.id(entry.link)
            feed_item.title(entry.title)
            feed_item.updated(self.ensure_tz_utc(entry.date))
            author = {"name": entry.author}
            if entry.author_uri:
                author['uri'] = entry.author_uri
            feed_item.author(author)
            feed_item.published(self.ensure_tz_utc(entry.date))
            feed_item.link(link={"href": entry.link, "rel": "alternate", "type": "text/html"})
            if entry.enclosures:
                for enclosure in entry.enclosures:
                    if enclosure.get("href"):
                        feed_item.enclosure(url=enclosure.get("href"), length=enclosure.get("length", 0),
                                            type=enclosure.get("type", ""))
            if use_summary and entry.summary:
                feed_item.summary(entry.summary_html)
            image_proxies = None
            if self.config.get('image_proxy_domains') and image_proxy_uri:
                image_proxies = {x: image_proxy_uri for x in self.config['image_proxy_domains']}
            content_html = entry.generate_image_html(image_proxies=image_proxies) + "\n" + entry.content_html
            feed_item.content(content=content_html, type="html")

        return fg.atom_str(pretty=True)






