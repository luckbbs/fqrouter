import logging
from gevent import subprocess
import gevent

LOGGER = logging.getLogger('fqrouter.%s' % __name__)

BUSYBOX_PATH = '/data/data/fq.router2/busybox'
PYTHON_PATH = '/data/data/fq.router2/python/bin/python-launcher.sh'
USE_SU = False


def launch_python(name, args, on_exit=None):
    command = [BUSYBOX_PATH, 'sh', PYTHON_PATH, '-m', name] + list(args)
    LOGGER.info('launch python: %s' % ' '.join(command))
    if USE_SU:
        proc = subprocess.Popen('su', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        proc.stdin.write(' '.join(command))
        proc.stdin.write('\n')
        proc.stdin.write('exit\n')
    else:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    gevent.sleep(0.5)
    if proc.poll() is not None:
        try:
            output, _ = proc.communicate()
            LOGGER.error('%s exit output: %s' % (name, output))
        except:
            LOGGER.exception('failed to log %s exit output' % name)
        raise Exception('failed to start %s' % name)
    LOGGER.info('%s started: %s' % (name, proc.pid))
    gevent.spawn(monitor_process, name, proc, on_exit)
    return proc


def monitor_process(name, proc, on_exit):
    try:
        output, _ = proc.communicate()
        if proc.poll():
            LOGGER.error('%s output: %s' % (name, output[-1000:]))
    except:
        LOGGER.exception('%s died' % name)
    finally:
        LOGGER.info('%s exited' % name)
        if on_exit:
            try:
                on_exit()
            except:
                LOGGER.exception('failed to execute on_exit hook for %s' % name)


def call(args):
    if USE_SU:
        proc = subprocess.Popen('su', stdin=subprocess.PIPE)
        proc.stdin.write(' '.join(args))
        proc.stdin.write('\n')
        proc.stdin.write('exit\n')
        proc.communicate()
        return proc.poll()
    else:
        return subprocess.call(args)


def check_call(args):
    if USE_SU:
        proc = subprocess.Popen('su', stdin=subprocess.PIPE)
        proc.stdin.write(' '.join(args))
        proc.stdin.write('\n')
        proc.stdin.write('exit\n')
        proc.communicate()
        if proc.poll():
            raise subprocess.CalledProcessError(proc.poll(), args)
        return 0
    else:
        return subprocess.check_call(args)


def check_output(args):
    if USE_SU:
        proc = subprocess.Popen('su', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        proc.stdin.write(' '.join(args))
        proc.stdin.write('\n')
        proc.stdin.write('exit\n')
        output = proc.communicate()[0]
        retcode = proc.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, args, output=output)
        return output
    else:
        return subprocess.check_output(args, stderr=subprocess.STDOUT)


def Popen(args, **kwargs):
    if USE_SU:
        proc = subprocess.Popen('su', stdin=subprocess.PIPE, **kwargs)
        proc.stdin.write(' '.join(args))
        proc.stdin.write('\n')
        proc.stdin.write('exit\n')
        return proc
    else:
        return subprocess.Popen(args, **kwargs)