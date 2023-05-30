
import json
from src.lib.validationlanguage.src_translator.hsdes import Article, HsdesAPI
from datetime import datetime
from src.lib.validationlanguage.src_translator.data import date_to_week, week_to_date

class Names:
    @classmethod
    def get_members(cls):
        list = []
        for member in dir(cls):
            if not callable(getattr(cls, member)) and not member.startswith("__"):
                attr = getattr(cls, member)
                list.append(attr)
        return list

    @classmethod
    def is_member(cls, m):
        return m in cls.get_members()


class Tcd(Article):
    class AUTO:
        POTENTIAL_NAME = "server_platf.test_case_definition.automation_potential"
        CMD_NAME = "server_platf.test_case_definition.command_line"
        COMMENT_NAME = "server_platf.test_case_definition.automation_comment"

        SOLUTION_NAME = "server_platf.test_case_definition.automation_current"
        STATUS_NAME = "server_platf.test_case_definition.automation_status"
        ETA_NAME = "server_platf.test_case_definition.automation_eta"

        class STATUS(Names):
            NEW = 'NEW'
            EXPLORATION = 'EXPLORATION'
            DEVELOP = 'In Progress'
            SCRIPT_READY = 'Automated'
            DEPLOYED = 'Deployed'
            REJECTED = 'Rejected'

        class POTENTIAL(Names):
            FULLY='Fully Automate'
            SEMI = 'Partial Automate'
            MANUAL = 'Manual'

        class SOLUTION(Names):
            MANUAL = 'Manual'
            MONTANA = 'Montana'
            CRAUTO = 'CRAuto'
            DTAF = 'DTAF'
            #PI = 'PI'

    @staticmethod
    def __to_int(value):
        auto_version = int(value.split('.')[0])
        code = value.split('.')[1]
        if code not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
            accept_status_number = 0
        else:
            accept_status_number = int(code)

        return auto_version, accept_status_number

    def __init__(self, json_data=None, id=None):
        super(Tcd, self).__init__(json_data, id)


    def update_auto_status(self, status):
        assert(Tcd.AUTO.STATUS.is_member(status))
        self.update_field(Tcd.AUTO.STATUS_NAME, status)

    def update_auto_eta(self, eta=None, inweek=True):
        now = datetime.now()
        if eta is None:
            #2022-01-01 00:00:00.0
            timestamp = now.strftime("%Y-%m-%d") + " 00:00:00.0"
        elif inweek:
            assert(isinstance(eta, str))
            # ETA = '2021wwxx.x'
            timestamp = week_to_date(eta) + " 00:00:00.0"
        else:
            assert (isinstance(eta, str))
            # ETA = 'YYYY-MM-DD'
            timestamp = eta + " 00:00:00.0"
        self.update_field(Tcd.AUTO.ETA_NAME, timestamp)




class TcdAPI(HsdesAPI):
    def __init__(self, tenant='server_platf', subject="test_case_definition"):
        super(TcdAPI, self).__init__(tenant, subject)
        self.ctype = Tcd

    def download_article(self, id, override=False):
        # type: (int, bool)->Tcd
        out = super(TcdAPI, self).download_article(id, override)
        assert(isinstance(out, Tcd))
        return out

if __name__ == '__main__':
    api = TcdAPI()
    a = api.download_article(16015342566)
    print("===============================================================")
    print(a.to_json())

    a.update_auto_eta()
    api.commit_article(16015342566)

