import sys, os
from collections import defaultdict
from flask import Flask, render_template, url_for, send_from_directory
from flask import Blueprint, g, current_app, Response
from flask_flatpages import FlatPages
from flask_frozen import Freezer, relative_url_for

from PIL import Image

import config
from curate_video import poster_filename_for

## originally had width="640" height="264" in video tag
videojs_template = """
<div align="center" class="embed-responsive embed-responsive-4by3">
<video id="{id}" class="video-js vjs-default-skin embed-responsive-item"
       controls preload="auto" poster="{poster_url}">
 <source src="{webm}" type="video/webm" />
 <source src="{mp4}" type="video/mp4" />
 <p>Your browser does not support this video content.</p>
</video>
</div>"""


## <source src="http://video-js.zencoder.com/oceans-clip.ogv" type='video/ogg' />
## <source src="http://video-js.zencoder.com/oceans-clip.webm" type='video/webm' />

class MediaType:
    image = "image"
    video = "video"
    other = "other"

def get_media_type(filename):
    extension = os.path.splitext(filename)[1].lower()
    if extension in (".jpeg", ".jpg"):
        return MediaType.image
    elif extension in (".mp4", ".webm", ".3pg", ".mov"):
        return MediaType.video
    return MediaType.other

def html_for_image(filename):
    url = relative_url_for("posts_bp.get_media", filename=filename)
    classes = "img-responsive img-rounded"
    img_tag = '<img class="{}" src="{}">'.format(
            classes, url)
    return '<a href="{}">{}</a>'.format(url, img_tag)

def html_for_media(filename):
    media_type = get_media_type(filename)
    url = relative_url_for("posts_bp.get_media", filename=filename)
    if media_type == MediaType.image:
        return html_for_image(filename)
    if media_type == MediaType.video:
        basename, ext = os.path.splitext(filename)
        fname_mp4, fname_webm = basename + ".mp4", basename + ".webm"
        fname_poster = poster_filename_for(filename)
        url_mp4 = relative_url_for("posts_bp.get_media", filename=fname_mp4)
        url_webm = relative_url_for("posts_bp.get_media", filename=fname_webm)
        poster_url = relative_url_for("posts_bp.get_media",
                                      filename=fname_poster)
        return videojs_template.format(
            id=filename, mp4=url_mp4, webm=url_webm, 
            poster_url=poster_url)

    return "<p>Unknown media type: '{}'</p>".format(filename)

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield tuple(l[i:i+n])

class Pagination(object):
    def __init__(self, pages, has_next, has_prev,
                 next_num, prev_num):
        self.items = pages
        self.has_next = has_next
        self.has_prev = has_prev
        self.next_num = next_num
        self.prev_num = prev_num

def compute_media_html(media_fnames):
    """ return list of html snippets for each media thing in input
    """
    type_to_names = defaultdict(list)
    for filename in media_fnames:
        type_to_names[get_media_type(filename)].append(filename)
    media_html = [html_for_media(fname) for fname in
                  type_to_names[MediaType.video]]

    tall_images, short_images = [], []
    for filename in type_to_names[MediaType.image]:
        im = Image.open(os.path.join(config.MEDIA_PATH, filename))
        width, height = im.size
        if height > width:
            tall_images.append(filename)
        else:
            short_images.append(filename)

    if len(tall_images) == 1:
        row = ['<div class="row">',
               '<div class="center-block col-sm-6" style="float: none;">']
        row.append(html_for_media(tall_images[0]))
        row.append("</div></div>")
        media_html.append("".join(row))
    else:
        for c in chunks(tall_images, 2):
            row = ['<div class="row top-buffer">',
                   '<div class="col-sm-6">']
            row.append(html_for_media(c[0]))
            row.append("</div>")
            if len(c) > 1:
                row.append('<div class="col-sm-6">')
                row.append(html_for_media(c[1]))
                row.append("</div>")
            row.append("</div>")
            media_html.append("".join(row))

    for fname in short_images:
        media_html.append(html_for_media(fname))

    return media_html

class PageCollection(object):
    def __init__(self, flatpages):
        self.pages = sorted(flatpages, key=lambda p: p["date"],
                            reverse=True)

    def compute_embedded_media(self):
        for page in self.pages:
            media_fnames = page.meta.get("media", [])
            page.meta["media_html"] = compute_media_html(media_fnames)

    def by_date(self, year, month, day=None):
        posts = []
        for post in self.pages:
            if (post["date"].year == year and
                post["date"].month == month and
                (day is None or post["date"].day == day)):
                posts.append(post)
        return Pagination(posts, False, 0, False, 0)

    def paginate(self, page, posts_per_page):
        start_idx = (page - 1) * posts_per_page
        subpages = self.pages[start_idx:start_idx + posts_per_page]
        has_prev = bool(page > 1)
        prev_num = page - 1
        has_next = bool(start_idx + posts_per_page < len(self.pages))
        next_num = page + 1

        return Pagination(subpages, has_next, has_prev,
                          next_num, prev_num)

posts_bp = Blueprint("posts_bp", __name__)

def create_app(config=config):# create the application object
    app = Flask(__name__)
    app.config.update(
        DEBUG=True,
        FLATPAGES_AUTO_RELOAD=True,
        FLATPAGES_EXTENSION=".md",
        FLATPAGES_ROOT=config.POSTS_PATH,
        FREEZER_RELATIVE_URLS=True,
        FREEZER_DESTINATION=config.BUILD_PATH,
        POSTS_PER_PAGE=config.POSTS_PER_PAGE,
        MEDIA_PATH=config.MEDIA_PATH
    )
    app.register_blueprint(posts_bp)
    raw_posts = FlatPages(app)
    def load_pages():
        all_posts = PageCollection(raw_posts)
        all_posts.compute_embedded_media()
        g.all_posts = all_posts
    app.before_request(load_pages)

    return app

def create_freezer(app):
    return Freezer(app)

@posts_bp.route("/")
@posts_bp.route("/page/<int:page>/")
def index(page=1):
    posts_per_page = current_app.config.get("POSTS_PER_PAGE")
    posts = g.all_posts.paginate(page, posts_per_page)
    return render_template(config.TEMPLATE_FILE, posts=posts)

@posts_bp.route("/<int:year>/<int:month>/")
@posts_bp.route("/<int:year>/<int:month>/<int:day>/")
def by_date(year, month, day=None):
    posts = g.all_posts.by_date(year, month, day)
    return render_template(config.TEMPLATE_FILE, posts=posts)

@posts_bp.route("/media/<string:filename>")
def get_media(filename):
    media_path = current_app.config.get("MEDIA_PATH")
    return send_from_directory(media_path, filename)

@posts_bp.route("/robots.txt")
def robots_txt():
    return Response("User-agent: *\nDisallow: /", mimetype="text/plain")

# start the server with the 'run()' method
if __name__ == '__main__':
    app = create_app(config)
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer = create_freezer(app)
        freezer.freeze()
    elif len(sys.argv) > 1 and sys.argv[1] == "deploy":
        os.system("{} sync {} {}".format(config.S3CMD_PATH,
            config.BUILD_DIR, config.S3BUCKET))
    else:
        app.run(debug=True)
