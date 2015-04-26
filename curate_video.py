import sys, os, shutil, glob
from contextlib import contextmanager

import config

@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

def rotate_video(filename):
    base, ext = os.path.splitext(filename)
    tmp_filename = "tmp" + ext
    os.system("{} -i {} -vf transpose=1 -c:a copy {}".format(
        config.AVCONV_PATH, filename, tmp_filename))
    os.unlink(filename)
    shutil.move(tmp_filename, filename)

## Very finnicky commands I found with a lot of searching on the web...
## These seem to work great for me, converting from mp4, MOV, and 3gp
## to mp4 and webm.
av_to_webm_cmd = "{} -i {} -c:v libvpx -b:v 128k -c:a libvorbis {}"
av_to_mp4_cmd = "{} -i {} -c:v libx264 -c:a libmp3lame -q:a 3 -ar:a 44100 {}"

def transcode(source, dest, codec):
    if codec == "webm":
        os.system(av_to_webm_cmd.format(config.AVCONV_PATH, source, dest))
    elif codec == "mp4":
        os.system(av_to_mp4_cmd.format(config.AVCONV_PATH, source, dest))
    else:
        assert False, "codec {} not recognized".format(codec)

def poster_filename_for(filename):
    basename, ext = os.path.splitext(filename)
    return basename + "-poster.jpg"

av_grab_frame_cmd = "{} -ss 0 -i {} -f image2 -vframes 1 {}"
def generate_poster(video_filename):
    poster_filename = poster_filename_for(video_filename)
    if not os.path.exists(poster_filename):
        os.system(av_grab_frame_cmd.format(
            config.AVCONV_PATH, video_filename, poster_filename))

def curate_directory(path):
    """ for each video in path, ensure that there are
    corresponding mp4 and webm videos.  Some phones seem
    to rotate the videos; you'll have to play around with this.
    """
    with cd(path):
        for filename in glob.glob("*.mp4"):
            generate_poster(filename)
            base, ext = os.path.splitext(filename)
            if not os.path.exists(base + ".webm"):
                rotate_video(filename)
                transcode(filename, base + ".webm", "webm")

        for extension in ("*.3gp", "*.mov", "*.MOV"):
            generate_poster(filename)
            for filename in glob.glob(extension):
                base, ext = os.path.splitext(filename)
                if not os.path.exists(base + ".mp4"):
                    transcode(filename, base + ".mp4", "mp4")
                if not os.path.exists(base + ".webm"):
                    transcode(filename, base + ".webm", "webm")

def main(argv):
    """ this script (sepcifically, `curate_directory`) is used in main.py to
    ensure we have videos in all the correct formats.  It can also be used
    standalone.  This is useful, for example, if you want to change encoding
    parameters, or especially if there are one or two videos that are
    sideways...
    """

    cmd = argv[1]
    media_path = config.MEDIA_PATH
    if cmd == "curate":
        curate_directory(media_path)
    elif cmd == "rotate":
        fname = argv[2]
        basename, ext = os.path.splitext(fname)
        with cd(media_path):
            for filename in glob.glob(basename + ".*"):
                rotate_video(filename)
    else:
        print ". curate - make the right video files"
        print ". rotate fname - rotate the corresponding videos"
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
