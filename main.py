import sys, os

import config
from from_email import fetch_new_posts, parse_message_parts
from curate_video import curate_directory
from sitebuilder import create_app, create_freezer

def deploy_s3(source, dest):
    os.system("{} sync {} {}".format(
        config.S3CMD_PATH, source, dest))

def next_path(path, basename, extension):
    """ return the next filename of the form
    path/basename-n.extension; in other words, find
    the smallest n such that this file does not exist
    """
    fname = os.path.join(path, basename + extension)
    if not os.path.exists(fname):
        return fname

    for i in range(2, 100):
        fname = os.path.join(path, "{}-{}{}".format(
            basename, i, extension))
        if not os.path.exists(fname):
            return fname

    assert False, "can't find filename w/ base {}".format(
            basename)

def add_and_render(posts_path, media_path, new_posts):
    for post in new_posts:
        post.write_attachments(media_path)
        post_path = next_path(posts_path, post.base_filename(), ".md")
        with open(post_path, "w") as f:
            f.write(post.to_markdown())

    flask_app = create_app(config)
    freezer = create_freezer(flask_app)
    freezer.freeze()

def is_sender_whitelisted(sender, whitelist):
    munged_sender = sender.replace(".", "")
    for snippet in whitelist:
        if snippet in munged_sender:
            return True
    return False

def filter_whitelist(posts, whitelist):
    return [p for p in posts
            if is_sender_whitelisted(p.sender, whitelist)]

def main(argv):
    """ fetch new mails, parse into posts, if there are new ones, append them
    to the list of posts and render website.
    """

    new_posts = fetch_new_posts(config.IMAP_SERVER,
                                config.IMAP_USERNAME,
                                config.IMAP_PASSWD)
    new_posts = filter_whitelist(new_posts, config.WHITELIST)
    if new_posts:
        for post in new_posts:
            post.fixup_date()
        curate_directory(config.MEDIA_PATH)
        add_and_render(config.POSTS_PATH, config.MEDIA_PATH, new_posts)
        deploy_s3(config.BUILD_PATH, config.S3BUCKET)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
