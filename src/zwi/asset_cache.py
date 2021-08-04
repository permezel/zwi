# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
#
# local asset cache
#
# This is not generally applicable to anything.
# I have a set of URLs being presented.
# They all have a common prefix, and a unique suffix representing the asset.
#
# The local f/s is used to cache them.
#
import os
import sys
import time

from .util import Error, error, debug, verbo, debug_p, verbo_p

import threading
import queue

class AssetCache(object):
    """Asset Cache class.
    Still under development, and not currently used for anything.
    I intend to use it perhaps eventually....
    """

    class Threads(threading.Thread):
        def __init__(self, cache):
            super().__init__()
            self._cache = cache
            pass

        def run(self):
            return self._cache.run(self)
        pass

    def __init__(self, path, callback):
        super().__init__()
        self._cache = {}
        self._threads = {}
        self._context = self._ssl_kluge()
        self._path = path   # get_zdir('.image-cache')
        self._cb = callback
        self._mux = threading.Lock()
        self._requ = queue.Queue(0)
        self._resp = queue.Queue(0)
        self._terminate = False
        self._nthreads = 0
        # ensure path has a trailing os.sep
        if self._path[-1] != os.sep:
            self._path += os.sep
            pass
        raise SystemExit('Write some more code....')

    def url_to_key(self, url):
        """Extract key from URL."""
        return url.split('/')[-1]

    def key_to_path(self, key):
        """Construct path from key."""
        if os.sep in key:
            return '/dev/null'
        return self._path + os.path.normpath(key)
    
    def load(self, url, widget):
        """Load an asset into the cache."""
        key = self.url_to_key(url)
        fna = self.key_to_path(key)
        print(f'load: {key=} {url=}')

        if url == 'None':
            return None

        self._mux.acquire()
        is_file = os.path.isfile(fna)
        if key in self._cache and is_file:
            rv = self._cache[key]
            assert rv == fna
        elif isfile:
            rv = self._cache[key] = fna
        else:
            self._cache[key] = rv = None
            self._requ.put((url, key, fna, widget))
            if self._nthreads == 0:
                thr = AssetCache.Threads(self)
                thr.start()
                pass
            pass
        self._mux.release()
        return rv

    def unload(self, url, delete=False):
        """Load an asset into the cache."""
        key = self.url_to_key(url)
        fna = self.key_to_path(key)

        print(f'unload: {key=} {fna=}')

        self._mux.acquire()
        if key in self._cache:
            rv = self._cache[key]
            if delete and os.path.isfile(fna):
                os.remove(fna)
                pass
            del self._cache[key]
        self._mux.release()
        return

    def stop(self):
        while True:
            self._mux.acquire()
            if self._nthreads > 0:
                self._terminate = True
                print('waiting for thread to terminate....')
            else:
                self._mux.release()
                return
            self._mux.release()
            pass
        pass

    def run(self, thr):
        """Thread function."""
        tid = threading.get_ident()

        self._mux.acquire()
        self._terminate = False
        self._threads[tid] = thr
        self._nthreads += 1
        print(f'adding thread {tid=} {self._nthreads=} {thr=}')
        self._mux.release()

        self._run()

        self._mux.acquire()
        self._nthreads -= 1
        print(f'deleting: {threading.get_ident()=} {tid=}')
        if tid in self._threads:
            del self._threads[tid]
        else:
            print(f'wtf? {tid=} {self._threads}')
            pass
        self._mux.release()
        print(f'thread {threading.get_ident()} {tid=} returns.')
        return

    def _run(self):
        while True:
            self._mux.acquire()
            if self._requ.qsize() == 0 or self._terminate:
                if self._requ.qsize() != 0:
                    debug(2, f'{self=} {self._terminate=} {self._nthreads=}')
                    self._terminate = False
                else:
                    self._mux.release()
                    return
                pass
            self._mux.release()

            try:
                wrk = self._requ.get(block=True, timeout=1)
            except Exception as ex:
                # print(f'{threading.get_ident()} {ex=}')
                wrk = None
                pass

            if wrk is None:
                continue

            print(f'{wrk=}')
            
            url, key, fna = wrk[0], wrk[1], wrk[2]
            if url == 'None' or 'http' not in url:
                continue  # some are None???

            if not os.path.isfile(fna):
                self._fetch(url, key, fna)
                pass

            print(f'{fna=} {os.path.isfile(fna)}')

            if os.path.isfile(fna):
                self._resp.put(wrk)
                self._cb(self)	# callback
                pass
            time.sleep(.001)
            pass
        pass

    @staticmethod
    def _ssl_kluge():
        """Need this to avoid certificate validation errors."""
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    def update(self, callback):
        print(f'update: {self._resp.qsize()=}')
        while self._resp.qsize() > 0:
            print(f'update: {self._resp.qsize()=}')
            while True:
                try:
                    wrk = self._resp.get(False)
                except Exception as ex:
                    wrk = None
                    break

                url, key, fna, wid = wrk[0], wrk[1], wrk[2], wrk[3]
                print(f'{key=}')
                # px = self._cache[key] = QPixmap(f'''{self._path}/{key.split('/')[-1]}''')
                # XXX: use the os.XXX functions?
                val = self._cache[key] = fna
                if callback:
                    callback(wrk)
                    pass
                pass

            # see if we are all done
            self._mux.acquire()
            if self._requ.qsize() == 0 and not self._terminate and self._nthreads > 0:
                # print(f'request thread to terminate')
                self._terminate = (self._resp.qsize() == 0)
                pass
            self._mux.release()
            pass
        pass

    def _fetch(self, url, key, path):
        """Try to fetch the resource and stack in file."""
        import shutil
        import urllib.request

        print(f'fetch: {key=} {url=}')

        try:
            with urllib.request.urlopen(url, context=self._context) as resp:
                f = open(path, 'wb')
                shutil.copyfileobj(resp, f)
                f.close()
        except Exception as e:
            print(f'oops: {key=} {url=} {e=}')
            self._mux.acquire()
            if key in self._cache:
                del self._cache[key]
                pass
            try:
                # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                # XXX massive security hole here???
                # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                os.remove(path)
            except Exception as e:
                pass
            self._mux.release()
            pass
        pass
    pass

