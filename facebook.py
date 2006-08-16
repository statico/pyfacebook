import urllib
import urllib2
import webbrowser
import md5
from time import time
from xml.dom.minidom import parseString



def _get_element_text(elem):
	"""Get a node's text by joining all of the text child nodes."""
	return ''.join(node.data for node in elem.childNodes if node.nodeType == node.TEXT_NODE)


class FacebookError(Exception):
	"""Exception class for errors received from Facebook."""
	def __init__(self, code, msg):
		self.code = code
		self.msg = msg
		print 'Error ' + code + ': ' + msg
	def __str__(self):
		return 'Error ' + code + ': ' + msg


class Facebook(object):
	def __init__(self, api_key, secret_key):
		self.api_key = api_key
		self.secret_key = secret_key
		self.secret = None

	def auth_createToken(self):
		result = self._call_method('facebook.auth.createToken', {})
		self.auth_token = result['token']
		return self.auth_token

	def auth_getSession(self):
		result = self._call_method('facebook.auth.getSession', {'auth_token': self.auth_token})
		self.session_key = result['session_key']
		self.uid = result['uid']
		self.secret = result['secret']
		return result

	def wall_getCount(self, user=None):
		if not user:
			user = self.uid
		return self._call_method('facebook.wall.getCount', {'id': user})

	def users_getInfo(self, users=None, fields=['name']):
		if not users:
			users = [self.uid]
		return self._call_method('facebook.users.getInfo', {'users': ','.join(users), 'fields': ','.join(fields)})

	def events_getInWindow(self, start, end):
		return self._call_method('facebook.events.getInWindow', {'start_time': str(start), 'end_time': str(end)})

	def pokes_getCount(self):
		return self._call_method('facebook.pokes.getCount', {})

	def photos_getAlbums(self, user=None):
		if not user:
			user = self.uid
		return self._call_method('facebook.photos.getAlbums', {'id': user})

	def photos_getCommentCount(self):
		return self._call_method('facebook.photos.getCommentCount')

	def photos_getFromAlbum(self, album):
		return self._call_method('facebook.photos.getFromAlbum', {'aid': album})

	def messages_getCount(self):
		return self._call_method('facebook.messages.getCount', {})

	def friends_get(self):
		return self._call_method('facebook.friends.get', {})

	def friends_areFriends(self, id1, id2):
		return self._call_method('facebook.friends.areFriends', {'id1': id1, 'id2': id2})

	def friends_getTyped(self, type):
		return self._call_method('facebook.friends.getTyped', {'link_type': type})

	def photos_getOfUser(self, user=None, max=20):
		if not user:
			user = self.uid
		return self._call_method('facebook.photos.getOfUser', {'id': user, 'max': str(max)})

	def login(self):
		webbrowser.open('http://api.facebook.com/login.php?api_key=' + self.api_key + '&auth_token=' + self.auth_token)



	def _parse_response_item(self, node):
		if len(filter(lambda x: x.nodeType == x.ELEMENT_NODE and x.nodeName.endswith('_elt'), node.childNodes)) > 0:
			return self._parse_response_list(node)
		elif len(filter(lambda x: x.nodeType == x.ELEMENT_NODE, node.childNodes)) > 0:
			return self._parse_response_dict(node)
		else:
			return _get_element_text(node)

	def _parse_response_dict(self, node):
		result = {}
		for item in filter(lambda x: x.nodeType == x.ELEMENT_NODE, node.childNodes):
			result[item.nodeName] = self._parse_response_item(item)
		if node.hasAttributes():
			if node.hasAttribute('id'):
				result['id'] = node.getAttribute('id')
		return result

	def _parse_response_list(self, node):
		result = []
		for item in filter(lambda x: x.nodeType == x.ELEMENT_NODE, node.childNodes):
			result.append(self._parse_response_item(item))
		return result
		

	def _check_error(self, dom):
		error = dom.getElementsByTagName('fb_error')
		if len(error) != 0:
			code = _get_element_text(error[0].getElementsByTagName('code')[0])
			msg = _get_element_text(error[0].getElementsByTagName('msg')[0])
			raise FacebookError(code, msg)
		return True

	def _arg_hash(self, args):
		hash = md5.new()
#		hash.update(''.join([urllib.urlencode({key: args[key]}) for key in sorted(args.keys())]))
		hash.update(''.join([key + '=' + args[key] for key in sorted(args.keys())]))
		if self.secret:
			hash.update(self.secret)
		else:
			hash.update(self.secret_key)
		return hash.hexdigest()

	def _call_method(self, method, args={}):
		args['api_key'] = self.api_key
		args['method'] = method

		if method not in ['facebook.auth.createToken', 'facebook.auth.getSession']:
			args['session_key'] = self.session_key
			args['call_id'] = str(int(time() * 1000))

		args['sig'] = self._arg_hash(args)

		if method == 'facebook.auth.getSession':
			xml = urllib2.urlopen('https://api.facebook.com/restserver.php', urllib.urlencode(args)).read()
		else:
			xml = urllib2.urlopen('http://api.facebook.com/restserver.php', urllib.urlencode(args)).read()

		dom = parseString(xml)
		self._check_error(dom)
		result = self._parse_response_item(dom)['result']
		dom.unlink()
		return result



if __name__ == '__main__':
	api_key = '1977d4ec72ee22eefb6c1ab26016e1e7'
	secret_key = '33bdd420a11c4d470cd2483ee9b08f09'

	facebook = Facebook(api_key, secret_key)

	facebook.auth_createToken()
	# Show login window
	facebook.login()

	# Login to the window, then press enter
	print 'After logging in, press enter...'
	raw_input()

	facebook.auth_getSession()
	info = facebook.users_getInfo([facebook.uid], ['name', 'birthday', 'affiliations', 'gender'])[0]

	print 'Name: ', info['name']
	print 'Birthday: ', info['birthday']
	print 'Gender: ', info['gender']

	friends = facebook.friends_get()
	friends = facebook.users_getInfo(friends[0:5], ['name', 'birthday'])

	for friend in friends:
		print friend['name'], 'has a birthday on', friend['birthday']
