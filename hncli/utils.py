'''
Utility module.
'''
import re


_none = object()

def cast(type_, val, default=_none):
	''' Casts value to given type with optional default. '''
	if default is _none:
		return type_(val)
	try:
		return type_(val)
	except ValueError:
		return default


def break_lines(text, max_length):
	''' Breaks given text into lines of given maximum length.
	Lines are only broken at the word boundaries.
	This function functions if text contains words longer
	than the maximum.
	'''
	words = re.split(r'\s+', text)

	res = []
	line = ""
	while words:
		word = words[0]
		if len(line + word) <= max_length:
			line += word
			if len(words) > 1:
				line += " "
			words = words[1:]
		else:
			res.append(line)
			line = ""

	if line:
		res.append(line)
	return res


## Getting terminal size
## (from: http://stackoverflow.com/a/6550596/434799)

def get_terminal_size():
	''' Retrieves size of terminal as 2-tuple: (width, height) '''
	import platform
	current_os = platform.system()
	tuple_xy = None
	if current_os == 'Windows':
	   tuple_xy = _get_terminal_size__windows()
	   if tuple_xy is None:
	      tuple_xy = _get_terminal_size__tput()
	      # needed for window's python in cygwin's xterm!
	if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
	   tuple_xy = _get_terminal_size__posix()
	if tuple_xy is None:
	   tuple_xy = (80, 25)      # default value
	return tuple_xy

def _get_terminal_size__windows():
    res = None
    try:
        from ctypes import windll, create_string_buffer

        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12

        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    except:
        return None
    if res:
        import struct
        (bufx, bufy, curx, cury, wattr,
         left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
        return sizex, sizey
    else:
        return None

def _get_terminal_size__tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
       import subprocess
       proc=subprocess.Popen(["tput", "cols"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
       output=proc.communicate(input=None)
       cols=int(output[0])
       proc=subprocess.Popen(["tput", "lines"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
       output=proc.communicate(input=None)
       rows=int(output[0])
       return (cols,rows)
    except:
       return None


def _get_terminal_size__posix():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,'1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (env['LINES'], env['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])
