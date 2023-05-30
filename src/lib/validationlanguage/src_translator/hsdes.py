import os
import requests
import json
from requests_kerberos import HTTPKerberosAuth
import urllib3
import base64

# this is to ignore the ssl insecure warning as we are passing in 'verify=false'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Article():

    def __init__(self, json_data=None, id=None):
        if json_data is not None:
            self.data = json_data['data'][0]
            self.modified = {}
            for i in self.data.keys():
                self.modified[i] = False
        else:
            assert (id is not None)
            self.data = {}
            self.modified = {}
        self.id = id

    @staticmethod
    def get_cmd():
        return 'article/%d'

    def get_field(self, key):
        return self.data[key]

    def update_field(self, key, value):
        self.data[key] = value
        self.modified[key] = True

    def merge(self, art):
        my_keys = self.data.keys()
        for key in art.data.keys():
            if key not in my_keys:
                self.data[key] = art.data[key]
                self.modified[key] = False

    def update(self, data):
        for k, v in data.keys():
            self.update_field(k, v)

    def modified_to_json(self):
        data = []

        for key in self.modified.keys():
            if self.modified[key]:
                data.append({key: self.data[key]})

        return data

    def to_json(self):
        data = []
        for key in self.modified.keys():
            data.append({key: self.data[key]})

        return data


class Query():
    def __init__(self, json_data=None):
        if json_data is None:
            self.data = []
        else:
            self.data = json_data['data']

    @property
    def length(self):
        return len(self.data)

    def get_id_list(self):
        ids = []
        for d in self.data:
            ids.append(int(d['id']))
        return ids

    def append_data(self, json_data):
        self.data.extend(json_data['data'])

    @staticmethod
    def get_cmd(start_at=1, max_results=1000, id_only=False):
        cmd = f'query/%d?start_at={start_at}&max_results={max_results}'
        if id_only:
            cmd += '&fields=id'
        return cmd

class HsdesAPI():
    SERVER = 'https://hsdes-api.intel.com/rest/'
    SERVER_AUTH = 'https://hsdes-api.intel.com/rest/auth/'
    REG_USER = 'HLS_USERNAME'
    REG_TOKEN = 'HLS_TOKEN'
    HEADER = {'Content-type': 'application/json'}

    def __init__(self, tenant='server_platf', subject="test_case_definition"):
        self.auth = HTTPKerberosAuth()
        self.tenant = tenant
        self.subject = subject
        self.articles = {}
        self.queries = {}
        self.ctype = Article

    def __auth_headers(self):
        user = os.environ.get(HsdesAPI.REG_USER)
        token = os.environ.get(HsdesAPI.REG_TOKEN)
        assert user is not None and token is not None, f'No base auth info set. Set system variable {HsdesAPI.REG_USER} and {HsdesAPI.REG_TOKEN} to enable base auth for HSDES and try again.'
        tok = user + ':' + token
        encoded_tok = base64.b64encode(tok.encode()).decode()
        return {'Content-Type': 'application/json', 'Authorization': f'Basic {encoded_tok}'}

    def __restful_get(self, url, *args):
        print(url)
        assert(len(args) % 2 == 0)

        response = requests.get(HsdesAPI.SERVER + url, verify=False, auth=self.auth, headers=HsdesAPI.HEADER)
        if response.reason == 'Unauthorized' or response.status_code == 401:
            response = requests.get(HsdesAPI.SERVER_AUTH + url, headers=self.__auth_headers(), verify=False)
            data = response.json()
            return data
        data = response.json()
        return data

    @staticmethod
    def get_url(cmd, *args):
        return cmd % args

    def __get_article(self, id):
        url = HsdesAPI.get_url(Article.get_cmd(), id)
        data = self.__restful_get(url)
        a = self.ctype(json_data=data)
        return a

    def commit_article(self, id):
        assert(id in self.articles.keys())
        url = HsdesAPI.get_url(Article.get_cmd(), id)
        d = self.articles[id].modified_to_json()
        if len(d) == 0:
            return False

        data = {
          "tenant": self.tenant,
          "subject": self.subject,
          "fieldValues": d
        }

        payload = json.dumps(data)
        print(payload)
        response = requests.put(HsdesAPI.SERVER + url, verify=False, auth=self.auth, headers=self.HEADER, data=payload)
        if response.reason == 'Unauthorized' or response.status_code == 401:
            response = requests.put(HsdesAPI.SERVER_AUTH + url, headers=self.__auth_headers(), verify=False, data=payload)
        print(response.text)
        return True

    def commit_all(self):
        for k in self.articles.keys():
            self.commit_article(k)

    def download_article(self, id, override=False):
        # type: (int, bool)->Article
        a = self.__get_article(id)
        if id in self.articles.keys() and not override:
            self.articles[id].merge(a)
        else:
            self.articles[id] = a
        return self.articles[id]


    def download_query(self, id):
        # type: (int)->Query
        query = Query()
        start = 1
        data_length = 100
        max_results = 100
        while data_length > 0 and data_length == max_results:
            url = HsdesAPI.get_url(Query.get_cmd(start_at=start, max_results=max_results), id)
            data = self.__restful_get(url)
            data_length = len(data['data'])
            query.append_data(data)
            start += max_results

        self.queries[id] = query
        return query

    def update_articles_in_batch(self, data):
        for tcd_id in data.keys():
            if tcd_id not in self.articles.keys():
                self.articles[tcd_id] = self.ctype(json_data=data[tcd_id])
            else:
                self.articles[tcd_id].update(data[tcd_id])

    def add_article(self, article):
        assert(isinstance(article, Article))
        if article.id in self.articles.keys():
            self.articles[id].merge(article)

def hsdes_query_ids(query_id):
    api = HsdesAPI()
    query = api.download_query(query_id)
    t = query.get_id_list()
    return t

if __name__ == '__main__':
    from datetime import datetime

    #api = HsdesAPI()
    #a=api.download_article(16015342566)
    print("===============================================================")
    #print(a.to_json())
    now = datetime.now()
    #timestamp = now.strftime("%Y-%m-%d, %H:%M:%S")

    # 2022-01-01 00:00:00.0
    timestamp = now.strftime("%Y-%m-%d") + " 00:00:00.0"
    print(timestamp)
    #a.update_field('title', 'test with timestamp ' + timestamp)
    #api.commit_all()