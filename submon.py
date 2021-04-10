#!/usr/bin/python3

# Visual Shell for Submonitor.

ROOT = '/var/mydata'
CMDS = {
  'sh': ['bash', '-c'],
  'jpg': ['qiv', '-f', '-m', '-i'],
  'mp4': ['vlc', '--fullscreen', '--gain=0.1'],
  'm3u8': ['xterm', '-fa', 'Monospace', '-fs', '32', '-fullscreen', '-e', 'vlc', '-I', 'ncurses', '-v', '2', '--volume', '127'],
}
TIMER = 60
hiddev = ''

import curses
import locale
import os
import signal
import subprocess

power_state = False

def finddev():
  devs = subprocess.check_output('udevadm info -q path /dev/hidraw*', shell=True).decode('utf_8').split('\n')
  for dev in devs:
    if dev.find(':16C0:05DF.') >= 0:
      return '/dev/' + dev[dev.rindex('/') + 1:]
  return ''

def power(state):
  global hiddev
  global power_state

  if state == power_state:
    return
  if not hiddev:
    hiddev = finddev()
  if not hiddev or not os.path.exists(hiddev) or not os.access(hiddev, os.W_OK):
    hiddev = ''
    return
  with open(hiddev, 'w') as f:
    if state:
      f.write('\x00\x01')
    else:
      f.write('\x00\x00')
  power_state = state

def power_handler(signo, frame):
  power(False)

def power_reset():
  power(True)
  signal.alarm(0)
  
def main(stdscr):
  power(True)
  signal.signal(signal.SIGALRM, power_handler)
  curses.mousemask(curses.ALL_MOUSE_EVENTS)
  curses.start_color()
  curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_YELLOW)
  curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
  curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLUE)
  curses.init_pair(6, curses.COLOR_RED, curses.COLOR_CYAN)
  list(stdscr, ROOT)


def list(stdscr, dir):
  if not (dir + '/').startswith(ROOT + '/'):
    dir = ROOT
  files = os.listdir(path=dir)
  files = [file for file in files if not file.startswith('.')]
  files.sort()
  attrs = [os.path.isdir(os.path.join(dir, file)) for file in files]

  curs = 0
  page = -1
  height, width = stdscr.getmaxyx()
  size = height - 2
  while True:
    # Update the screen.
    stdscr.clear()
    # Header
    stdscr.addstr(0, 0, dir[len(ROOT):] + '/', curses.color_pair(1))
    # Body
    page = curs // size
    for i in range(size):
      if size * page + i >= len(files):
        break
      file = files[size * page + i]
      attr = attrs[size * page + i]
      line = file.encode('euc_jp', errors='ignore')[:width - 1].decode('euc_jp', errors='ignore')
      stdscr.addstr(1 + i, 0, line, curses.color_pair(4 if attr else 2))
    # Footer
    line = '%d/%d' % (curs + 1, len(files))
    stdscr.addstr(height - 1, 0, line, curses.color_pair(6))
    # Cursor
    file = files[curs]
    attr = attrs[curs]
    line = file.encode('euc_jp', errors='ignore')[:width - 1].decode('euc_jp', errors='ignore')
    stdscr.addstr(1 + curs - size * page, 0, line, curses.color_pair(5 if attr else 3))
    stdscr.refresh()

    # Process input.
    key = stdscr.getch()
    mouse = curses.getmouse()[4] if key == curses.KEY_MOUSE else 0
    if key == curses.KEY_UP or mouse == 65536:
      power_reset()
      curs = max(0, curs - 1)
    elif key == curses.KEY_DOWN or mouse == 2097152:
      power_reset()
      curs = min(len(files) - 1, curs + 1)
    elif key == curses.KEY_LEFT:
      power_reset()
      curs = max(0, curs - size)
    elif key == curses.KEY_RIGHT:
      power_reset()
      curs = min(len(files) - 1, curs + size)
    elif key == ord('\n') or mouse == curses.BUTTON1_CLICKED:
      power_reset()
      path = os.path.join(dir, files[curs])
      if attrs[curs]:
        list(stdscr, path)
      else:
        run(path)
      page = -1
    elif key == curses.KEY_BACKSPACE or key == ord('\b') or mouse == curses.BUTTON3_CLICKED:
      power_reset()
      break
    else:
      continue
    signal.alarm(TIMER)

def run(path):
  suff = os.path.basename(path).split('.')[-1]
  if suff not in CMDS:
    return
  realpath = os.path.realpath(path)
  subprocess.run(['xbindkeys'])
  subprocess.run(CMDS[suff] + [realpath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  subprocess.run(['killall', 'xbindkeys'])

if __name__ == '__main__':
  locale.setlocale(locale.LC_ALL, '')
  curses.wrapper(main)
