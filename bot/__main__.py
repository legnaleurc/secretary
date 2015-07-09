import sys
import functools
import re
import inspect
import random

from tornado import ioloop, gen, options
from telezombie import api

from . import settings, db


class KelThuzad(api.TeleLich):

    def __init__(self, api_token):
        super(KelThuzad, self).__init__(api_token)

        self._text_handlers = []

    @gen.coroutine
    def on_text(self, message):
        id_ = message.message_id
        chat = message.chat
        text = message.text
        for handler in self._text_handlers:
            result = handler(message)
            if result:
                yield self.send_message(chat.id_, result, reply_to_message_id=id_)
                break
        else:
            print(message.text)

    def add_text_handlers(self, handlers):
        self._text_handlers.extend(handlers)


def command_filter(pattern):
    def real_decorator(fn):
        @functools.wraps(fn)
        def callee(*args, **kwargs):
            spec = inspect.getfullargspec(fn)
            if 'self' in spec.args:
                self = args[0]
                message = args[1]
            else:
                self = None
                message = args[0]

            m = re.match(pattern, message.text.strip())
            if not m:
                return None
            args = m.groups()

            if self:
                return fn(self, message, *args)
            else:
                return fn(message, *args)
        return callee
    return real_decorator


class YPCHandler(object):

    def __init__(self):
        pass

    @command_filter(r'^/ypc$')
    def ypc(self, message, *args, **kwargs):
        with db.Session() as session:
            murmur = session.query(db.Murmur).all()
            if not murmur:
                return None
            mm = random.choice(murmur)
            return mm.sentence

    @command_filter(r'^/ypc\s+add\s+(.+)$')
    def ypc_add(self, message, *args, **kwargs):
        with db.Session() as session:
            mm = db.Murmur(sentence=args[0])
            session.add(mm)
            session.commit()
            return str(mm.id)

    @command_filter(r'^/ypc\s+remove\s+(\d+)$')
    def ypc_remove(self, message, *args, **kwargs):
        try:
            with db.Session() as session:
                mm = session.query(db.Murmur).filter_by(id=int(args[0]))
                session.delete(mm)
                return str(mm.id)
        except Exception:
            return None

    @command_filter(r'^/ypc\s+list$')
    def ypc_list(self, message, *args, **kwargs):
        o = ['']
        with db.Session() as session:
            murmur = session.query(db.Murmur)
            for mm in murmur:
                o.append('{0}: {1}'.format(mm.id, mm.sentence))
        return '\n'.join(o)


class MemeHandler(object):

    def __init__(self):
        pass

    @command_filter(r'^/meme\s+(\S+)$')
    def get(self, message, *args, **kwargs):
        with db.Session() as session:
            mm = session.query(db.Meme).filter_by(name=args[0]).first()
            if not mm:
                return None
            return mm.url

    @command_filter(r'^/meme\s+add\s+(\S+)\s+(\S+)$')
    def set_(self, message, *args, **kwargs):
        with db.Session() as session:
            mm = db.Meme(name=args[0], url=args[1])
            session.add(mm)
            session.commit()
            return mm.url

    @command_filter(r'^/meme\s+remove\s+(\S+)$')
    def unset(self, message, *args, **kwargs):
        try:
            with db.Session() as session:
                mm = session.query(db.Meme).filter_by(name=args[0])
                session.delete(mm)
                return mm.name
        except Exception:
            return None

    @command_filter(r'^/meme\s+list$')
    def list_(self, message, *args, **kwargs):
        o = ['']
        with db.Session() as session:
            meme = session.query(db.Meme)
            for mm in meme:
                o.append(mm.name)
        return '\n'.join(o)


@gen.coroutine
def forever():
    api_token = options.options.api_token

    kel_thuzad = KelThuzad(api_token)
    ypc = YPCHandler()
    meme = MemeHandler()

    kel_thuzad.add_text_handlers([
        ypc.ypc,
        ypc.ypc_add,
        ypc.ypc_remove,
        ypc.ypc_list,
        meme.set_,
        meme.unset,
        meme.list_,
        meme.get,
    ])

    yield kel_thuzad.poll()


def parse_config(path):
    data = settings.load(path)
    options.options.api_token = data['api_token']
    options.options.database = data['database']


def main(args=None):
    if args is None:
        args = sys.argv

    options.define('config', default=None, type=str, help='config file path', metavar='telezombie.yaml', callback=parse_config)
    options.define('api_token', default=None, type=str, help='API token', metavar='<token>')
    options.define('database', default=None, type=str, help='database URI', metavar='<uri>')
    remains = options.parse_command_line(args)

    main_loop = ioloop.IOLoop.instance()

    main_loop.run_sync(forever)

    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
