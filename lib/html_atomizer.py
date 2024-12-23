from lib.atomizer import Entry, Page
import parsel
import dateutil.parser
import datetime

class HTMLPage(Page):

    def parse_entries_from_response(self, response):
        return self.parse_entries_from_html(response.text)

    def parse_entries_from_html(self, html):
        parsed_entries = []
        selector = parsel.Selector(html)
        entries = selector.xpath(self.config['entries'])
        self.title = selector.xpath("//head/title/text()").get() or self.title
        self.itunes_category = selector.xpath(self.config['itunes_category']).get() if self.config.get(
            'itunes_category') else self.config.get("itunes_category_default")
        self.itunes_explicit = selector.xpath(self.config['itunes_explicit']).get() if self.config.get(
            'itunes_explicit') else self.config.get("itunes_explicit_default")
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