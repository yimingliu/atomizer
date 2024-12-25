from lib.atomizer import Entry, Page
import parsel
import dateutil.parser
import datetime

class HTMLPage(Page):

    def parse_entries_from_response(self, response):
        return self.parse_entries_from_html(response.text)

    def get_xpath_scalar(self, selector, key, default=None):
        val = self.get_xpath_value(selector, key)
        if val:
            val = val.get()
        return val.strip() if val else self.config.get(f"{key}_default", default)

    def get_xpath_list(self, selector, key, default=None):
        val = self.get_xpath_value(selector, key)
        if val:
            val = val.getall()
        return [x.strip() for x in val if x] if val else self.config.get(f"{key}_default", default)

    def get_xpath_value(self, selector, key):
        path = self.config.get(key)
        if path:
            return selector.xpath(path)

    def parse_entries_from_html(self, html):
        parsed_entries = []
        selector = parsel.Selector(html)
        entries = selector.xpath(self.config['entries'])
        self.title = self.get_xpath_scalar(selector, 'feed_title') or selector.xpath("//head/title/text()").get() or self.title
        self.itunes_category = self.get_xpath_scalar(selector, 'itunes_category')
        self.itunes_explicit = self.get_xpath_scalar(selector, 'itunes_explicit')
        if entries:
            for entry in entries:
                link = self.get_xpath_scalar(entry, 'link')
                if not link:
                    continue
                date = self.get_xpath_scalar(entry, 'date')
                item = Entry(link=link,
                             title=self.get_xpath_scalar(entry, 'title', default=link),
                             date=dateutil.parser.parse(date) if date else datetime.datetime.now(datetime.timezone.utc),
                             author=self.get_xpath_scalar(entry, 'author', default=""),
                             author_uri=self.get_xpath_scalar(entry, 'author_uri', default=""),
                             summary=self.get_xpath_list(entry, 'summary') or [],
                             image=self.get_xpath_list(entry, 'image') or [])
                parsed_entries.append(item)
        if parsed_entries:
            parsed_entries.sort(key=lambda x: x.date, reverse=True)
        return parsed_entries
