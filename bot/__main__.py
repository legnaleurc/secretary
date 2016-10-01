if __name__ == '__main__' and __package__ == '':
    import os, sys, importlib
    parent_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(os.path.dirname(parent_dir))
    __package__ = os.path.basename(parent_dir)
    importlib.import_module(__package__)


import sys
import functools
import re
import inspect
import random
import functools
import json
import collections

from tornado import ioloop, gen, options, web, log, httpserver, httpclient, process
from telezombie import api

from . import settings, db


class KelThuzad(api.TeleLich):

    def __init__(self, api_token):
        super(KelThuzad, self).__init__(api_token)

        self._text_handlers = []

    def add_text_handlers(self, handlers):
        self._text_handlers.extend(handlers)

    @property
    def text_handlers(self):
        return self._text_handlers


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


class UpdateHandler(api.TeleHookHandler):

    @gen.coroutine
    def on_text(self, message):
        id_ = message.message_id
        chat = message.chat
        text = message.text
        lich = self.settings['lich']
        for handler in lich.text_handlers:
            result = yield handler(message)
            if result:
                yield lich.send_message(chat.id_, result, reply_to_message_id=id_)
                break
        else:
            print('update handler: ', message.text)


class NOPHandler(web.RequestHandler):

    def get(self):
        print('??')

    def post(self):
        print(self.request.body)


class FallbackHandler(object):

    def __init__(self):
        self._chat_buffer = collections.deque(maxlen=16)

    @gen.coroutine
    @command_filter(r'^s([^\r\n\\].{3,})$')
    def sed(self, message, *args, **kwargs):
        tmp = args[0]
        delimiter, tmp = tmp[0], tmp[1:]
        tmp = re.match(r'[^{0}]+{0}[^{0}]*{0}[gi]*'.format(delimiter), tmp)
        if not tmp:
            return None
        tmp = yield self._sed(message.text, message.from_.id_)
        if not tmp:
            return None
        return '更正:\n{0}'.format(tmp)

    @gen.coroutine
    @command_filter(r'^.+$')
    def cyclic_buffer(self, message, *args, **kwargs):
        msg, user_id = message.text, message.from_.id_
        self._chat_buffer.appendleft((msg, user_id))
        return None

    @gen.coroutine
    def _sed(self, pattern, user_id):
        buffer_ = filter(lambda _: _[1] == user_id, self._chat_buffer)
        buffer_ = map(lambda _: _[0], buffer_)
        for msg in buffer_:
            try:
                new_msg = yield shell_out('sed', '-e', pattern, stdin=msg)
            except Exception as e:
                raise
                continue
            if new_msg == msg:
                continue
            return new_msg
        return None


class TwitchPuller(object):

    def __init__(self, kel_thuzad, channel_name):
        self._kel_thuzad = kel_thuzad
        self._channel_name = channel_name
        self._is_online = False
        url = 'https://api.twitch.tv/kraken/streams/{0}'.format(self._channel_name)
        self._curl = httpclient.AsyncHTTPClient()
        self._request = httpclient.HTTPRequest(url, headers={
            'Accept': 'application/vnd.twitchtv.v3+json',
        })
        self._chat_id = -16028742
        self._line = (
            '我廢，我宅，我實況',
            '唔哦！好實況，不看嗎？',
            '牛魔王，跟上帝出來看娘子！',
            '玩遊戲就是要實況啊，不然要幹麻？',
            '你知道你媽在這裡開實況嗎？',
        )

    @gen.coroutine
    def __call__(self):
        try:
            data = yield self._curl.fetch(self._request)
            data = data.body.decode('utf-8')
            data = json.loads(data)
        except Exception as e:
            print(e)
            return

        if self._is_online:
            if data['stream'] is None:
                self._is_online = False
        else:
            if data['stream'] is not None:
                self._is_online = True
                line = random.choice(self._line)
                yield self._kel_thuzad.send_message(self._chat_id, '{0}\nhttp://www.twitch.tv/{1}'.format(line, self._channel_name))


@gen.coroutine
@command_filter(r'^/help(@\S+)?$')
def help(message, *args, **kwargs):
    return '\n'.join((
        '',
        'sed <pattern>',
    ))


@gen.coroutine
def shell_out(*args, **kwargs):
    stdin = kwargs.get('stdin', None)
    if stdin is not None:
        p = process.Subprocess(args, stdin=process.Subprocess.STREAM, stdout=process.Subprocess.STREAM)
        yield p.stdin.write(stdin.encode('utf-8'))
        p.stdin.close()
    else:
        p = process.Subprocess(args, stdout=process.Subprocess.STREAM)
    out = yield p.stdout.read_until_close()
    exit_code = yield p.wait_for_exit(raise_error=True)
    return out.decode('utf-8')


@gen.coroutine
def forever():
    api_token = options.options.api_token

    kel_thuzad = KelThuzad(api_token)
    fallback = FallbackHandler()

    kel_thuzad.add_text_handlers([
        help,
        fallback.sed,
        fallback.cyclic_buffer,
    ])

    yield kel_thuzad.poll()


@gen.coroutine
def setup():
    api_token = options.options.api_token
    dsn = options.options.database
    db.prepare(dsn)

    kel_thuzad = KelThuzad(api_token)
    fallback = FallbackHandler()

    kel_thuzad.add_text_handlers([
        help,
        fallback.sed,
        fallback.cyclic_buffer,
    ])

    application = web.Application([
        (r'^/{0}$'.format(api_token), UpdateHandler),
        (r'.*', NOPHandler),
    ], lich=kel_thuzad)
    application.listen(8443)

    twitch_users = (
        'inker610566',
        'legnaleurc',
        'markseinn',
        'vaporting',
        'wonwon0102',
    )
    twitch_daemons = (TwitchPuller(kel_thuzad, _) for _ in twitch_users)
    twitch_daemons = (ioloop.PeriodicCallback(_, 5 * 60 * 1000) for _ in twitch_daemons)
    for daemon in twitch_daemons:
        daemon.start()

    yield kel_thuzad.listen('https://www.wcpan.me/bot/{0}'.format(api_token))


def parse_config(path):
    data = settings.load(path)
    options.options.api_token = data['api_token']
    options.options.database = data['database']


def main(args=None):
    if args is None:
        args = sys.argv

    log.enable_pretty_logging()
    options.define('config', default=None, type=str, help='config file path', metavar='telezombie.yaml', callback=parse_config)
    options.define('api_token', default=None, type=str, help='API token', metavar='<token>')
    options.define('database', default=None, type=str, help='database URI', metavar='<uri>')
    remains = options.parse_command_line(args)

    main_loop = ioloop.IOLoop.instance()

    main_loop.add_callback(setup)

    main_loop.start()
    main_loop.close()

    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
