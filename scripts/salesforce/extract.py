from apps.salesforce.syncer import ini
import traceback
import sys


def run(*args):
    try:
        ini()

    except Exception as ex:
        print("Log This: Unexpected Exception Exception Details: {}".format(ex))
        print("-"*60)
        traceback.print_exc(file=sys.stdout)
        print("-"*60)
