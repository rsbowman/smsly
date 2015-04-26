from unittest import TestCase, main
import pickle, json
from datetime import datetime

from from_email import parse_message_parts, Post
from curate_video import poster_filename_for
import sitebuilder
from main import is_sender_whitelisted, filter_whitelist

class ParseEmailTests(TestCase):
    def test_parse_subject(self):
        with open("test_data/test_mail_subject.pickle", "r") as f:
            message_parts = pickle.load(f)
        post = parse_message_parts(message_parts)
        self.assertEqual(post._subject, "The sample title")
        self.assertEqual(post._body[:10], "This is a ")
        self.assertEqual(len(post._attachments), 0)
        self.assertEqual(post._date.strftime("%Y %m %d"),
                         "2015 03 29")

    def test_parse_image(self):
        with open("test_data/test_mail_image.pickle", "r") as f:
            message_parts = pickle.load(f)

        post = parse_message_parts(message_parts)
        self.assertEqual(post._subject, "")
        self.assertEqual(len(post._body), 48)
        self.assertEqual(len(post._attachments), 1)
        self.assertTrue("20150329_155012.jpeg" in post._attachments)

    def test_parse_video(self):
        with open("test_data/test_mail_video.pickle", "r") as f:
            message_parts = pickle.load(f)

        post = parse_message_parts(message_parts)
        self.assertEqual(post._subject, "")
        self.assertEqual(len(post._attachments), 1)
        self.assertTrue("20150328_100104_001.mp4" in post._attachments)

    def test_to_markdown(self):
        with open("test_data/test_mail_subject.pickle", "r") as f:
            message_parts = pickle.load(f)
        post = parse_message_parts(message_parts)
        markdown = post.to_markdown().splitlines()
        self.assertEqual(markdown[0], "date: 2015-03-29 17:46:43")
        self.assertEqual(markdown[1], "title: The sample title")
        self.assertEqual(markdown[2], "media: []")
        self.assertEqual(markdown[3], "")
        self.assertEqual(markdown[4][:15], "This is a test ")

class PostTests(TestCase):
    def test_add_subject(self):
        p = Post()
        self.assertEqual(p._subject, "")
        p.add_subject(None)
        self.assertEqual(p._subject, "")
        p.add_subject("a sub")
        self.assertEqual(p._subject, "a sub")

    def test_basic_post(self):
        p = Post()
        md_lines = p.to_markdown().splitlines()
        self.assertEqual(md_lines[0][:5], "date:")
        self.assertEqual(md_lines[1], "title: ")
        self.assertEqual(md_lines[2], "media: []")

    def test_fixup_dates(self):
        now = datetime.now()
        p = Post()
        p.add_body("This is a regular post")
        p.add_date(now)
        p.fixup_date()
        self.assertEqual(p._date, now)

        new_date = datetime(2015, 6, 17)
        p.add_body("{} This is an anachronism".format(
            new_date.strftime("%Y-%m-%d")))
        self.assertEqual(p._date, now)
        p.fixup_date()
        self.assertEqual(p._date, new_date)
        self.assertEqual(p._body, "This is an anachronism")

class SiteBuilderTests(TestCase):
    def setUp(self):
        class TestConfig(object):
            POSTS_PATH="test_posts"
            BUILD_PATH="test_build"
            MEDIA_PATH="test_media"
            POSTS_PER_PAGE=5
        self.app = sitebuilder.create_app(TestConfig())
        self.test_client = self.app.test_client()

    def test_html_for_image(self):
        filename = "boo.png"
        with self.app.test_request_context("/"):
            html = sitebuilder.html_for_image(filename)
            self.assertIn("src=\"media/" + filename, html)

    def test_html_for_media(self):
        with self.app.test_request_context("/"):
            html = sitebuilder.html_for_media("test.mp4")
            self.assertIn("<video ", html)
            self.assertIn("test.webm", html)
            self.assertIn("test.mp4", html)

    def test_get_media_type(self):
        for fname in ("doo.jpeg", "doo.JPEG", "doo.jpg", "doo.JPG"):
            self.assertEqual(sitebuilder.get_media_type(fname),
                             sitebuilder.MediaType.image)
        for fname in ("doo.mp4", "doo.webm", "doo.3pg", "doo.mov",
                      "doo.MOV"):
            self.assertEqual(sitebuilder.get_media_type(fname),
                             sitebuilder.MediaType.video)
        for fname in ("doo.txt", "foo.png", "wok.tar.gz"):
            self.assertEqual(sitebuilder.get_media_type(fname),
                             sitebuilder.MediaType.other)

    def test_compute_media_html(self):
        """ TODO: figure out how to test; this
        looks up image width and height using PIL..
        """
        pass

    def test_index(self):
        rv = self.test_client.get("/")
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Bowman", rv.data)

class CurateVideoTests(TestCase):
    def test_poster_filename(self):
        self.assertEqual(poster_filename_for("boopie.png"),
                         "boopie-poster.jpg")

class MainTests(TestCase):
    def test_is_whitelisted(self):
        whitelist = ["abc", "123"]
        self.assertTrue(is_sender_whitelisted("a.bc@gmail.com", whitelist))
        for sender in ("a.bc@gmail.com", "glad_abc", "jimmy123@hotmail"):
            self.assertTrue(is_sender_whitelisted(sender, whitelist))
        for sender in ("a@bc.com", "124@hotmail.com"):
            self.assertFalse(is_sender_whitelisted(sender, whitelist))

if __name__ == '__main__':
    main()
