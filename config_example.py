import os

LOGFILE = "from_email.log"

BASE_PATH = "/path/to/website"
POSTS_PATH = os.path.join(BASE_PATH, "posts")
MEDIA_PATH = os.path.join(BASE_PATH, "media")
BUILD_PATH = os.path.join(BASE_PATH, "build/")
## trailing slash necessary above for s3cmd to properly
## copy files recursively

POSTS_PER_PAGE = 5
TEMPLATE_FILE = "index.html"

IMAP_SERVER="imap.example.com"
IMAP_USERNAME="johnsmith@yahoo.com"
IMAP_PASSWD="passwd"

WHITELIST=[
    "johnsmith",
    "40442677888", ## johnsmith's phone number
    ]

S3CMD_PATH = "/usr/bin/s3cmd"
AVCONV_PATH = "/usr/bin/avconv"

S3BUCKET = "s3://my-website-bucket/"
