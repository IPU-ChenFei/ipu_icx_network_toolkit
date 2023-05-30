import sys


class Logger:
    def info(self, message):
        print(message, file=sys.stdout)

    def error(self, message):
        print(message, file=sys.stderr)


logger = Logger()