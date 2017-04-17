import unittest
from utils import utf8,escapeMarkdown,checkAndFixUrl,splitEmail

class UtilsTestCase(unittest.TestCase):
    """Tests for `utils.py`."""

    def test_solo_hostname(self):
        """Solo hostname"""
        self.assertEqual('http://prueba.com',checkAndFixUrl('prueba.com'))

    def test_hostname_puerto(self):
        """Hostname y puerto"""
        self.assertEqual('http://prueba.com:8181',checkAndFixUrl('prueba.com:8181'))

    def test_hostname_puerto_www(self):
        """Hostname, www y puerto"""
        self.assertEqual('http://www.prueba.com:8181',checkAndFixUrl('www.prueba.com:8181'))

    def test_solo_hostname_www(self):
        """Hostname y www"""
        self.assertEqual('http://www.prueba.com',checkAndFixUrl('www.prueba.com'))

    def test_hostname_puerto_www_path(self):
        """Hostname, www, puerto y path"""
        self.assertEqual('http://www.prueba.com:8181/youtrack',checkAndFixUrl('www.prueba.com:8181/youtrack'))

    def test_hostname_puerto_path(self):
        """Hostname, puerto y path"""
        self.assertEqual('http://prueba.com:8181/youtrack',checkAndFixUrl('prueba.com:8181/youtrack'))

    def test_hostname_path(self):
        """Hostname y path"""
        self.assertEqual('http://prueba.com/youtrack',checkAndFixUrl('prueba.com/youtrack'))

    def test_ip(self):
        """Ip"""
        self.assertEqual('http://127.0.0.1',checkAndFixUrl('127.0.0.1'))

    def test_ip_puerto(self):
        """Ip y puerto"""
        self.assertEqual('http://127.0.0.1:8989',checkAndFixUrl('127.0.0.1:8989'))

    def test_ip_puerto_path(self):
        """Ip, path y puerto"""
        self.assertEqual('http://127.0.0.1:8989/youtrack',checkAndFixUrl('127.0.0.1:8989/youtrack'))

    def test_split_email_user(self):
        """User comun"""
        username,email = splitEmail('rsperoni')
        self.assertEqual('rsperoni',username)
        self.assertIs(email,None)

    def test_split_email(self):
        """User email"""
        username,email = splitEmail('rsperoni@mgcoders.com')
        self.assertEqual('rsperoni',username)
        self.assertEqual('rsperoni@mgcoders.com',email)

if __name__ == '__main__':
    unittest.main()
