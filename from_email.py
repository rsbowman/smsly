import os, imaplib, email, json
from datetime import datetime
import logging

import config

logging.basicConfig(filename=config.LOGFILE, level=logging.DEBUG)

class Post(object):
    def __init__(self):
        self._date = datetime.now()
        self._body = ""
        self._subject = ""
        self._attachments = {}
        self._sender = None

    def add_body(self, body):
        self._body = body

    def add_subject(self, subject):
        if subject is not None:
            self._subject = subject

    def add_date(self, date):
        self._date = date

    sender = property(lambda s: s._sender)

    def add_sender(self, sender):
        self._sender = sender

    def add_attachment(self, filename, data):
        self._attachments[filename] = data

    def base_filename(self):
        return self._date.strftime("%Y_%m_%d")

    def to_markdown(self, date_format="%Y-%m-%d %H:%M:%S"):
        metadata = ["date: {}".format(self._date.strftime(date_format)),
                    "title: {}".format(self._subject),
                    "media: {}".format(self._attachments.keys())
                    ]
        return "\n".join(metadata) + "\n\n" + self._body

    def write_attachments(self, media_path):
        for filename, data in self._attachments.items():
            file_path = os.path.join(media_path, filename)
            curpath = os.path.abspath(os.curdir)
            with open(file_path, "w") as f:
                f.write(data)

    def fixup_date(self):
        """ if body begins with date, let that be the date
        of the post.
        """
        possible_date = self._body[:10]
        try:
            date = datetime.strptime(possible_date, "%Y-%m-%d")
        except ValueError:
            pass
        else:
            self._date = date
            self._body = self._body[10:].strip()

class FetchException(Exception):
    pass

def parse_message_parts(message_parts):
    new_post = Post()
    email_body = message_parts[0][1]
    mail = email.message_from_string(email_body)
    subject = mail["Subject"]
    date_tuple = email.utils.parsedate_tz(mail["Date"])

    if date_tuple:
        local_date = datetime.fromtimestamp(
            email.utils.mktime_tz(date_tuple))
    else:
        local_date = datetime.now()
        logging.warning("no date; using {}".format(local_date))

    new_post.add_subject(subject)
    new_post.add_date(local_date)
    new_post.add_sender(mail["From"])

    for part in mail.walk():
        content_type = part.get_content_maintype()
        if content_type in ("image", "video"):
            filename = part.get_filename()
            if filename:
                new_post.add_attachment(
                    filename, part.get_payload(decode=True))
            else:
                logging.warning(
                    "content_type is image but no filename: {}".format(
                        part.as_string()))
        elif content_type == "text":
            new_post.add_body(part.get_payload(decode=True))
    return new_post

def get_new_posts(imap_conn):
    imap_conn.select("INBOX")
    typ, data = imap_conn.search(None, "UNSEEN")
    if typ != "OK":
        raise FetchException("Error searching Inbox: {}".format(typ))

    posts = []
    for msg_id in data[0].split():
        typ, message_parts = imap_conn.fetch(msg_id, "(RFC822)")

        if typ != "OK":
            raise FetchException("Error fetching mail: {}".format(typ))

        new_post = parse_message_parts(message_parts)
        if new_post:
            posts.append(new_post)

    return posts

def fetch_new_posts(domain, username, passwd):
    conn = imaplib.IMAP4_SSL(domain)
    typ, _ = conn.login(username, passwd)

    if typ != "OK":
        raise FetchException("Not able to sign in: typ={}".format(
            typ))

    posts = get_new_posts(conn)

    conn.close()
    conn.logout()

    return posts

