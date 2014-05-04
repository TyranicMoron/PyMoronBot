from IRCMessage import IRCMessage
from IRCResponse import IRCResponse, ResponseType
from CommandInterface import CommandInterface
import WebUtils
from Data.api_keys import load_key
from Data import ignores

import re
import HTMLParser
import json
import math
from bs4 import BeautifulSoup
from twisted.words.protocols.irc import assembleFormattedText, attributes as A

class Command(CommandInterface):
    acceptedTypes = ['PRIVMSG','ACTION']
    help = 'automatic function that follows urls and grabs information about the resultant webpage'
    
    htmlParser = HTMLParser.HTMLParser()
    
    graySplitter = assembleFormattedText(A.normal[' ', A.fg.gray['|'], ' '])

    def onStart(self):
        self.youtubeKey = load_key(u'YouTube')
        self.imgurClientID = load_key(u'imgur Client ID')

    def shouldExecute(self, message):
        if message.Type not in self.acceptedTypes:
            return False
        if ignores.ignoreList is not None:
            if message.User.Name.lower() in ignores.ignoreList:
                return False
        return True
    
    def execute(self, message):
        match = re.search(r'(?P<url>(https?://|www\.)[^\s]+)', message.MessageString, re.IGNORECASE)
        if not match:
            return
        
        youtubeMatch = re.search(r'(youtube\.com/watch.+v=|youtu\.be/)(?P<videoID>[^&#\?]+)', match.group('url'))
        imgurMatch   = re.search(r'(i\.)?imgur\.com/(?P<imgurID>[^\.]+)', match.group('url'))
        twitterMatch = re.search(r'twitter.com/(?P<tweeter>[^/]+)/status(es)?/(?P<tweetID>[0-9]+)', match.group('url'))
        steamMatch   = re.search(r'store.steampowered.com/app/(?P<steamAppID>[0-9]+)', match.group('url'))
        ksMatch      = re.search(r'kickstarter.com/projects/(?P<ksID>[^/]+/[^/&#\?]+)', match.group('url'))
        twitchMatch  = re.search(r'twitch\.tv/(?P<twitchChannel>[^/]+)', match.group('url'))
        
        if youtubeMatch:
            return self.FollowYouTube(youtubeMatch.group('videoID'), message)
        elif imgurMatch:
            return self.FollowImgur(imgurMatch.group('imgurID'), message)
        elif twitterMatch:
            return self.FollowTwitter(twitterMatch.group('tweeter'), twitterMatch.group('tweetID'), message)
        elif steamMatch:
            return self.FollowSteam(steamMatch.group('steamAppID'), message)
        elif ksMatch:
            return self.FollowKickstarter(ksMatch.group('ksID'), message)
        elif twitchMatch:
            return self.FollowTwitch(twitchMatch.group('twitchChannel'), message)
        elif not re.search('\.(jpe?g|gif|png|bmp)$', match.group('url')):
            return self.FollowStandard(match.group('url'), message)
        
    def FollowYouTube(self, videoID, message):
        if self.youtubeKey is None:
            return IRCResponse(ResponseType.Say, '[YouTube API key not found]', message.ReplyTo)

        url = 'https://gdata.youtube.com/feeds/api/videos/{0}?v=2&key={1}'.format(videoID, self.youtubeKey)
        
        webPage = WebUtils.FetchURL(url)
        webPage.Page = webPage.Page.decode('utf-8')
        
        titleMatch = re.search('<title>(?P<title>[^<]+?)</title>', webPage.Page)
        
        if titleMatch:
            lengthMatch = re.search("<yt:duration seconds='(?P<length>[0-9]+?)'/>", webPage.Page)
            descMatch = re.search("<media:description type='plain'>(?P<desc>[^<]+?)</media:description>", webPage.Page)
            
            title = titleMatch.group('title')
            title = self.htmlParser.unescape(title)
            length = lengthMatch.group('length')
            m, s = divmod(int(length), 60)
            h, m = divmod(m, 60)
            if h > 0:
                length = u'{0:02d}:{1:02d}:{2:02d}'.format(h,m,s)
            else:
                length = u'{0:02d}:{1:02d}'.format(m,s)

            description = u'<no description available>'
            if descMatch:
                description = descMatch.group('desc')
                description = re.sub('<[^<]+?>', '', description)
                description = self.htmlParser.unescape(description)
                description = re.sub('\n+', ' ', description)
                description = re.sub('\s+', ' ', description)
                if len(description) > 150:
                    description = description[:147] + u'...'
                
            return IRCResponse(ResponseType.Say, self.graySplitter.join([title, length, description]), message.ReplyTo)
        
        return
    
    def FollowImgur(self, id, message):
        if self.imgurClientID is None:
            return IRCResponse(ResponseType.Say, '[imgur Client ID not found]', message.ReplyTo)

        if id.startswith('gallery/'):
            id = id.replace('gallery/', '')

        url = ''
        albumLink = False
        if id.startswith('a/'):
            id = id.replace('a/', '')
            url = 'https://api.imgur.com/3/album/{0}'.format(id)
            albumLink = True
        else:
            url = 'https://api.imgur.com/3/image/{0}'.format(id)

        headers = [('Authorization', 'Client-ID {0}'.format(self.imgurClientID))]
        
        webPage = WebUtils.FetchURL(url, headers)
        
        if webPage is None:
            url = 'https://api.imgur.com/3/gallery/{0}'.format(id)
            webPage = WebUtils.FetchURL(url, headers)

        if webPage is None:
            return
        
        response = json.loads(webPage.Page)
        
        imageData = response['data']

        if imageData['title'] is None:
            url = 'https://api.imgur.com/3/gallery/{0}'.format(id)
            webPage = WebUtils.FetchURL(url, headers)
            if webPage is not None:
                imageData = json.loads(webPage.Page)['data']

            if imageData['title'] is None:
                webPage = WebUtils.FetchURL('http://imgur.com/{0}'.format(id))
                imageData['title'] = self.GetTitle(webPage.Page).replace(' - Imgur', '')
                if imageData['title'] == 'imgur: the simple image sharer':
                    imageData['title'] = None
        
        data = []
        if imageData['title'] is not None:
            data.append(imageData['title'])
        else:
            data.append(u'<No Title>')
        if imageData['nsfw']:
            data.append(u'\x034\x02NSFW!\x0F')
        if albumLink:
            data.append(u'Album: {0} Images'.format(imageData['images_count']))
        else:
            if imageData.has_key('is_album') and imageData['is_album']:
                data.append(u'Album: {0:,d} Images'.format(len(imageData['images'])))
            else:
                if imageData[u'animated']:
                    data.append(u'\x032\x02Animated!\x0F')
                data.append(u'{0:,d}x{1:,d}'.format(imageData['width'], imageData['height']))
                data.append(u'Size: {0:,d}kb'.format(int(imageData['size'])/1024))
        data.append(u'Views: {0:,d}'.format(imageData['views']))
        
        return IRCResponse(ResponseType.Say, self.graySplitter.join(data), message.ReplyTo)

    def FollowTwitter(self, tweeter, tweetID, message):
        webPage = WebUtils.FetchURL('https://twitter.com/{0}/status/{1}'.format(tweeter, tweetID))

        soup = BeautifulSoup(webPage.Page)

        tweet = soup.find(class_='permalink-tweet')
        
        user = tweet.find(class_='username').text

        tweetText = tweet.find(class_='tweet-text')

        links = tweetText.find_all('a', {'data-expanded-url' : True})
        for link in links:
            link.string = link['data-expanded-url']

        embeddedLinks = tweetText.find_all('a', {'data-pre-embedded' : 'true'})
        for link in embeddedLinks:
            link.string = link['href']

        text = re.sub('[\r\n]+', self.graySplitter, tweetText.text)

        formatString = unicode(assembleFormattedText(A.normal[A.bold['{0}:'], ' {1}']))

        return IRCResponse(ResponseType.Say, formatString.format(user, text), message.ReplyTo)

    def FollowSteam(self, steamAppId, message):
        webPage = WebUtils.FetchURL('http://store.steampowered.com/app/{0}/'.format(steamAppId))

        soup = BeautifulSoup(webPage.Page)

        data = []
        title = soup.find(class_='apphub_AppName')
        if title is not None:
            data.append(title.text.strip())

        details = soup.find(class_='details_block')
        if details is not None:
            genres = 'Genres: ' + ', '.join([link.text for link in details.select('a[href*="/genre/"]')])
            data.append(genres)
            releaseDate = re.findall(u'Release Date\: .+', details.text, re.MULTILINE | re.IGNORECASE)[0]
            data.append(releaseDate)
            
        description = soup.find(class_='game_description_snippet')
        if description is not None:
            limit = 200
            description = description.text.strip()
            if len(description) > limit:
                description = '{0} ...'.format(description[:limit].rsplit(' ', 1)[0])
            data.append(description)

        return IRCResponse(ResponseType.Say, self.graySplitter.join(data), message.ReplyTo)

    def FollowKickstarter(self, ksID, message):
        webPage = WebUtils.FetchURL('https://www.kickstarter.com/projects/{0}/'.format(ksID))

        soup = BeautifulSoup(webPage.Page)

        data = []

        title = soup.find(id='title')
        if title is not None:
            creator = soup.find(id='name')
            if creator is not None:
                data.append(assembleFormattedText(A.normal['{0}', A.fg.gray[' by '], '{1}']).format(title.text.strip(), creator.text.strip()))
            else:
                data.append(title.text.strip())

        stats = soup.find(id='stats')

        backerCount = stats.find(id='backers_count')
        if backerCount is not None:
            data.append('Backers: {0:,}'.format(int(backerCount['data-backers-count'])))

        pledged = stats.find(id='pledged')
        if pledged is not None:
            pledgedString = assembleFormattedText(A.normal['Pledged: {0:,.0f}',A.fg.gray['/'],'{1:,.0f} {2} ({3:,.0f}% funded)'])
            data.append(pledgedString.format(float(pledged['data-pledged']),
                                             float(pledged['data-goal']),
                                             pledged.data['data-currency'],
                                             float(pledged['data-percent-raised']) * 100))

        findState = soup.find(id='main_content')
        if 'Project-state-canceled' in findState['class']:
            data.append(assembleFormattedText(A.normal[A.fg.red['Cancelled']]))
            
        elif 'Project-state-failed' in findState['class']:
            data.append(assembleFormattedText(A.normal[A.fg.red['Failed']]))

        elif 'Project-state-successful' in findState['class']:
                data.append(assembleFormattedText(A.normal[A.fg.green['Successful']]))

        elif 'Project-state-live' in findState['class']:
            duration = stats.find(id='project_duration_data')

            if duration is not None:
                remaining = float(duration['data-hours-remaining'])
                days = math.floor(remaining/24)
                hours = remaining/24 - days

                data.append('Duration: {0:.0f} days {1:.1f} hours to go'.format(days, hours))

        return IRCResponse(ResponseType.Say, self.graySplitter.join(data), message.ReplyTo)

    def FollowTwitch(self, channel, message):
        # Heavily based on Didero's DideRobot code for the same
        # https://github.com/Didero/DideRobot/blob/06629fc3c8bddf8f729ce2d27742ff999dfdd1f6/commands/urlTitleFinder.py#L37
        # TODO: viewer count and other stats?
        chanData = {}
        channelOnline = False
        twitchHeaders = [('Accept', 'application/vnd.twitchtv.v2+json')]
        webPage = WebUtils.FetchURL(u'https://api.twitch.tv/kraken/streams/{0}'.format(channel), twitchHeaders)

        streamData = json.loads(webPage.Page)

        if 'stream' in streamData and streamData['stream'] is not None:
            chanData = streamData['stream']['channel']
            channelOnline = True
        elif 'error' not in streamData:
            webPage = WebUtils.FetchURL(u'https://api.twitch.tv/kraken/channels/{0}'.format(channel), twitchHeaders)
            chanData = json.loads(webPage.Page)

        if len(chanData) > 0:
            if channelOnline:
                channelInfo = assembleFormattedText(A.fg.green['']) + '{0}'.format(chanData['display_name']) + assembleFormattedText(A.normal[''])
            else:
                channelInfo = assembleFormattedText(A.fg.red['']) + '{0}'.format(chanData['display_name']) + assembleFormattedText(A.normal[''])
            channelInfo += u' "{0}"'.format(re.sub('[\r\n]+', self.graySplitter, chanData['status'].strip()))
            if chanData['game'] is not None:
                channelInfo += assembleFormattedText(A.normal[A.fg.gray[', playing '], '{0}'.format(chanData['game'])])
            if chanData['mature']:
                channelInfo += assembleFormattedText(A.normal[A.fg.lightRed[' [Mature]']])
            if channelOnline:
                channelInfo += assembleFormattedText(A.normal[A.fg.green[' (Live with {0:,d} viewers)'.format(streamData['stream']['viewers'])]])
            else:
                channelInfo += assembleFormattedText(A.normal[A.fg.red[' (Offline)']])

            return IRCResponse(ResponseType.Say, channelInfo, message.ReplyTo)
    
    def FollowStandard(self, url, message):
        webPage = WebUtils.FetchURL(url)
        
        if webPage is None:
            return
        
        title = self.GetTitle(webPage.Page)
        if title is not None:
            return IRCResponse(ResponseType.Say, u'{0} (at {1})'.format(title, webPage.Domain), message.ReplyTo)
        
        return

    def GetTitle(self, webpage):
        match = re.search('<title\s*>\s*(?P<title>.*?)</title\s*>', webpage, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group('title')
            title = title.decode('utf-8')
            title = re.sub('(\n|\r)+', '', title)
            title = title.strip()
            title = re.sub('\s+', ' ', title)
            title = re.sub('<[^<]+?>', '', title)
            title = self.htmlParser.unescape(title)
            
            if len(title) > 300:
                title = title[:300] + "..."
            
            return title
        
        return None