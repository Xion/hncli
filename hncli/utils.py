'''
Utility module.
'''


def cast(type_, val, default=None):
	''' Casts value to given type with optional default. '''
	if default is None:
		return type_(val)
	try:
		return type_(val)
	except ValueError:
		return default