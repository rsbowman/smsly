# Smsly
## Static website, from text messages

Problem: I want to remember the beautiful moments from day to day, capturing
pictures and videos and thoughs as I go along.  But I'm lazy.  Probably won't
keep up with a traditional journal/website/blog.

However, I do always have my phone on me, and I'm constantly texting people
pictures and videos and little messages.  Why not do the same to an address
that collects these and makes a cute little static website out of them?

That's what Smsly does.  It also has a dumb name.  It's also completely
unsupported, hard to get working, and may delete all your files.  Use at your
own peril.

To use smsly you'll need at least these things:

* Flask, Flask-FlatPages, Frozen-Flask
* avconv (for transcoding video)
* s3cmd (if you want to host your website on Amazon S3)
* PIL or Pillow

## Setup (Roughly)

You'll want to rename `config_example.py` to `config.py` and change it to suit
your needs.  Set up an email account accessible by IMAP (I'm using a gmail
account, you may need to make modifications to `from_email.py` if you're using
a different provider).  The main program fetches new emails from this account,
stores them along with their attachements in the location you described in the
`config.py`, and, if there are new emails, renders the site and uploads it to
S3.  There are some various conveniences along the way, such as markdown
support and a whitelist (to make sure no Viagra commercials end up on your
website).

Note that you'll need a pretty recent version of `avconv` in order to transcode
video to formats readable by desktop browsers and mobile phones.  I had to
compile mine with lots of weird codecs, too, but I'm sure you can figure that
out.

Good luck!
