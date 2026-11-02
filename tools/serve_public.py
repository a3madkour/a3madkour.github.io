#!/usr/bin/env python3
"""Serve ./public for the Playwright suite.

`python3 -m http.server` listens with a queue of 5. Parallel browsers overflow
it, a refused connection drops a stylesheet or script, and a random 3-6 tests
fail per run on macOS.
"""
import functools
import http.server
import sys


class Server(http.server.ThreadingHTTPServer):
    request_queue_size = 128


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def main():
    port, directory = int(sys.argv[1]), sys.argv[2]
    handler = functools.partial(Handler, directory=directory)
    Server(("127.0.0.1", port), handler).serve_forever()


if __name__ == "__main__":
    main()
