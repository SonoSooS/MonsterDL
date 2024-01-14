from html.parser import HTMLParser


class WebJSONExtractor(HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.extracting = False
        self.content = None
    
    def handle_starttag(self, tag: str, attrs: 'list[tuple[str, str | None]]') -> None:
        if tag != 'script':
            return
        
        if ('type', 'application/json') not in attrs:
            return
        
        assert not self.extracting
        self.extracting = True
    
    def handle_endtag(self, tag: str) -> None:
        if not self.extracting:
            return
        
        assert tag == 'script'
        self.extracting = False
    
    def handle_data(self, data: str) -> None:
        if not self.extracting:
            return
        
        assert self.content is None
        self.content = data
