import pywikibot
import re
import pandas as pd

class Article:

    site = pywikibot.Site('en', 'wikipedia')

    def __init__(self, title):
        self.title = title
        self.revs_fetched = False
        self.page = pywikibot.Page(self.site, self.title)
    
    def __str__(self):
        if self.revs_fetched is False:
            info = "Article('{title}')".format(
                title=self.title
            )
        else:
            info = "Article('{title}', {numrev} revisions)".format(
                title=self.title,
                numrev=self.num_rev
            )
        return info

    def __repr__(self):
        return str(self)

    def get_revisions(self, spec='all', starttime=None, endtime=None):
        if spec is 'all':
            total = None
        elif isinstance(spec, int):
            total = spec
        else:
            raise TypeError("Revision specification must be an integer or 'all'!")
        # the following may break for articles with very long histories
        self.rev_data = list(self.page.revisions(
            total=total,
            content=False,
            starttime=starttime,
            endtime=endtime,
            reverse=True
        ))
        self.num_rev = len(list(self.rev_data))
        self.revs_fetched = True
        print('Successfully fetched data for {num_rev} revisions.'.format(
            num_rev=self.num_rev
        ))

    def ids(self):
        if not self.revs_fetched:
            raise Exception('No revision data fetched!')
        else:
            return [ rev.revid for rev in self.rev_data ]

    def sizes(self):
        if not self.revs_fetched:
            raise Exception('No revision data fetched!')
        else:
            return [ rev.size for rev in self.rev_data ]            
    
    def timestamps(self, date_format='isostring'):
        if not self.revs_fetched:
            raise Exception('No revision data fetched!')
        else:
            if date_format is 'wiki':
                return [ rev.timestamp.totimestampformat() for rev in self.rev_data ]
            elif date_format is 'isostring':
                return [ rev.timestamp.isoformat() for rev in self.rev_data ]
            elif date_format is 'unix':
                return [ rev.timestamp.timestamp() for rev in self.rev_data ]
            else:
                raise Exception('Unknown date format!')

    def to_data_frame(self, date_format='isostring', index=None):
        df = pd.DataFrame()
        df['rev_id'] = self.ids()
        df['timestamp'] = self.timestamps()
        df['size'] = self.sizes()
        if index is not None:
            df['line'] = index
            df = df[['line', 'rev_id', 'timestamp', 'size']]
        return df
    
    def linked(self, dist=1, return_strings=False, return_collection=False):
        if dist > 2:
            raise Exception('Linked articles only supported up to 2nd neighbour!')
        linked = re.findall(r'\[\[([^\]#\|]+)[^\[]*\]\]', self.page.text)
        linked = list(set(linked))
        if return_strings and return_collection:
            raise Exception('Clashing options for return type!')
        if dist is 1:
            if return_strings:
                return linked
            elif return_collection:
                return ArticleCollection(linked)
            else:
                return [Article(name) for name in linked]
        elif dist is 2:
            linked2nd = []
            for name in linked:
                linked2nd.extend(Article(name).linked(return_strings=True))
            linked2nd = list(set(linked2nd))
            if return_strings:
                return linked2nd
            elif return_collection:
                return ArticleCollection(linked2d)
            else:
                return [Article(name) for name in linked2nd]

class ArticleCollection():

    def __init__(self, articles=[]):

        self.titles = []
        self.articles = []

        type_error = TypeError('ArticleCollection expects a list of strings or Articles!')

        if type(articles) is not list:
            raise type_error
        for art in articles:
            if type(art) is str:
                self.titles.append(art)
                self.articles.append(Article(art))
            elif type(art) is Article:
                self.titles.append(art.title)
                self.articles.append(art)
            else:
                raise type_error

    def __repr__(self):
        if len(self) is 0:
            return 'ArticleCollection()'
        elif len(self) < 5:
            out_str = 'ArticleCollection([\n'
            for title in self.titles:
                out_str += '\t' + title + ',\n'
            out_str = out_str[:-2] + '\n])'
            return out_str
        elif len(self) > 5:
            return 'ArticleCollection(<{} Articles>)'.format(
                len(self)
            )

    def __str__(self):
        return repr(self)

    def __len__(self):
        return len(self.titles)

    def add(self, articles):

        type_error = TypeError('ArticleCollection expects a string or Article '
            'or a list of strings or Articles!')

        if type(articles) not in [str, Article, list]:
            raise type_error

        if type(articles) in [str, Article]:
            articles = [articles]

        for art in articles:
            if type(art) is str and art not in self.titles:
                self.titles.append(art)
                self.articles.append(Article(art))
            elif type(art) is Article and art.title not in self.titles:
                self.titles.append(art.title)
                self.articles.append(art)
            else:
                raise type_error

    def get_revisions(self, spec='all', starttime=None, endtime=None):
        if spec is 'all':
            total = None
        elif type(spec) is int:
            total = spec
        elif type(spec) is list:
            if len(spec) is not len(self.titles):
                raise Exception('Length of spec must match length of collection!')
        else:
            raise TypeError("Revision specification must be an integer or 'all' or a list of specs!")

        if type(spec) is not list:
            for art in self.articles:
                art.get_revisions(spec=spec, starttime=starttime, endtime=endtime)
        else:
            for art, s in zip(self.articles, spec):
                art.get_revisions(spec=s, starttime=starttime, endtime=endtime)


    def to_data_frame(self, date_format='isostring'):
        df = pd.DataFrame()
        for i, art in enumerate(self.articles):
            if not art.revs_fetched:
                raise Exception("No revision data fetched for Article '{title}'!".format(
                    title=art.title))
            df = df.append(art.to_data_frame(date_format=date_format, index=i))
        return df.reset_index(drop=True)