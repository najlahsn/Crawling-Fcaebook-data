
import urllib2
import json
import datetime
import csv
import time
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

app_id = "APP_ID"
app_secret = "APP_SECRET"  # DO NOT SHARE WITH ANYONE!
file_id = "FILE_ID"

access_token = app_id + "|" + app_secret

def unicode_normalize(text):
    return text.translate({ 0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 
                            0x201D:0x22, 0xa0:0x20 }).encode('utf-8')

def request_until_succeed(url):
    req = Request(url)
    success = False
    while success is False:
        try:
            response = urlopen(req)
            if response.getcode() == 200:
                success = True
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL {}: {}".format(url, datetime.datetime.now()))
            print("Retrying.")

    return response.read()

# Needed to write tricky unicode correctly to csv


def unicode_decode(text):
    try:
        return text.encode('utf-8').decode()
    except UnicodeDecodeError:
        return text.encode('utf-8')


def getFacebooklikeFeedUrl(base_url,page_id):

    # Construct the URL string
    node = "/%s/likes?limit=5000" % page_id 

    parameters = "&access_token=%s" % (access_token)
    url = base_url + node + parameters
    return url


def processFacebooklike(like, status_id):

    # The status is now a Python dictionary, so for top-level items,
    # we can simply call the key.

    # Additionally, some items may not always exist,
    # so must check for existence first

    like_author_id = unicode_normalize(like["id"])
    like_author_name = unicode_normalize(like["name"])


    # Return a tuple of all processed data

    return (status_id, like_author_id, like_author_name)
           

def scrapeFacebookPageFeedLikes(page_id, access_token):
    with open('{}_FB_ManyPosts_likes.csv'.format(file_id), 'w') as file:
        w = csv.writer(file)
        w.writerow(["status_id", "like_auther_id", "like_author_name"])

        num_processed = 0
        scrape_starttime = datetime.datetime.now()
        after = ''
        base = "https://graph.facebook.com/v2.9"
        parameters = "/?limit={}&access_token={}".format(
            2000, access_token)

        print("Scraping {} likes From Posts: {}\n".format(
            file_id, scrape_starttime))

        with open('{}_facebook_statuses_x.csv'.format(file_id), 'r') as csvfile:
            reader = csv.DictReader(csvfile)

            # Uncomment below line to scrape comments for a specific status_id
            # reader = [dict(status_id='5550296508_10154352768246509')]

            for status in reader:
                has_next_page = True

                while has_next_page:

                    node = "/{}/likes".format(status['status_id'])
                    after = '' if after is '' else "&after={}".format(after)
                    base_url = base + node + parameters + after

                    url = getFacebooklikeFeedUrl(base_url,page_id)
                    # print(url)
                    likes = json.loads(request_until_succeed(url))
                   
                    for like in likes['data']:
                        like_data = processFacebooklike(
                            like, status['status_id'])
                        w.writerow(like_data)
                                 
                        num_processed += 1
                        if num_processed % 2000 == 0:
                            print("{} likes Processed: {}".format(
                                num_processed, datetime.datetime.now()))

                    if 'paging' in likes:
                        if 'next' in likes['paging']:
                            after = likes['paging']['cursors']['after']
                        else:
                            has_next_page = False
                    else:
                        has_next_page = False

        print("\nDone!\n{} Comments Processed in {}".format(
            num_processed, datetime.datetime.now() - scrape_starttime))


if __name__ == '__main__':
   scrapeFacebookPageFeedLikes(file_id, access_token)
