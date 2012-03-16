'''
Utility module.
'''

_none = object()

def cast(type_, val, default=_none):
	''' Casts value to given type with optional default. '''
	if default is _none:
		return type_(val)
	try:
		return type_(val)
	except ValueError:
		return default