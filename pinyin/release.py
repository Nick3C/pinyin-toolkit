#!/usr/bin/env python

import os
import re
import subprocess
import sys
import time

import pinyin.utils


#
# Code from ActiveState recipe (http://code.activestate.com/recipes/146306/)
#

import httplib, mimetypes, mimetools, urllib2, cookielib

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)

def post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    headers = {'Content-Type': content_type,
               'Content-Length': str(len(body))}
    r = urllib2.Request("http://%s%s" % (host, selector), body, headers)
    return urllib2.urlopen(r).read()

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = mimetools.choose_boundary()
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

#
# End code from ActiveState recipe
#

def parse_releases(text):
    # Drop everything before the Changelog line
    text = text[text.find("h1. Changelog"):]
    
    # Split changelog into releases (the first list element is just from before the first release)
    for raw_release in text.split("h2. ")[1:]:
        m = re.match("Version ([^ ]+) \(([^\)]+)\)", raw_release)
        yield m.group(1), m.group(2), raw_release

def preflight_checks(repo_dir):
    errors = []
    
    def visit(_arg, dirname, names):
        for name in names:
            full_path = os.path.join(dirname, name)
            # See http://code.google.com/p/anki/issues/detail?id=1342&colspec=ID%20Type%20Status%20Priority%20Stars%20Summary
            if os.path.isfile(full_path) and os.path.getsize(full_path) == 0L:
                errors.append(full_path + " is 0 bytes long - a bug found in Anki 0.9.9.8.5 means that such files are not extracted")
    
    os.path.walk(repo_dir, visit, None)
    
    return errors

def build_release(credentials, release_info, temp_dir):
    # 1) Clone the whole repository to a fresh location -
    # this ensures we don't have any crap in the release
    temp_repo_dir = os.path.join(temp_dir, "repo")
    repo_dir = pinyin.utils.toolkitdir()
    print "Cloning current repo state to", temp_repo_dir
    subprocess.check_call(["git", "clone", repo_dir, temp_repo_dir])
    
    # 1.5) Sanity check directory
    errors = preflight_checks(temp_repo_dir)
    if len(errors) > 0:
        print "\n".join(errors)
        sys.exit(1)
    
    # 2) Build a ZIP of that fresh checkout, excluding the .git directory
    # and using maximal compression (-9) since the file is pretty big
    zip_file = os.path.join(temp_dir, "pinyin-toolkit.zip")
    repo_contents = [f for f in os.listdir(temp_repo_dir) if f[0] != '.']
    subprocess.check_call(["zip", "-9", "-r", zip_file] + repo_contents, cwd=temp_repo_dir)
    
    # 3) Upload to Anki
    upload_to_anki_online(credentials, release_info, zip_file)

def upload_to_anki_online(credentials, release_info, zip_file):
    # Login form (at http://anki.ichi2.net/account/login)
    # <form action="../account/login" method="post">
    #  <input type="text" name="username" value="" /></td>
    #  <input type="password" name="password" value="" /></td>
    #  <input type="hidden" name="submitted" value="1">
    #  <input type="submit" value="Login" />
    #  <input type="submit" value="Sign Up" />
    # </form>
    print "Logging in to the Anki website as", credentials["username"]
    post_multipart("anki.ichi2.net", "/account/login",
        [("username", credentials["username"]), ("password", credentials["password"]), ("submitted", "1")],
        [])
    
    # Upload form (at http://anki.ichi2.net/file/upload?id=423)
    # <form action="/file/upload" enctype="multipart/form-data" method="post">
    #   <input name="type" type="hidden" value="plugin">
    #   <input type="text" name="title" maxlength=60 size=60 value="Testing plugin upload protocol">
    #   <input name="file" type="file" size=50>
    #   <input type="text" name="tags" size=60 value="">
    #   <textarea rows=5 cols=60 name="description"></textarea>
    #   <input name="id" type="hidden" value="423">
    #   <input name="submit" type="submit" value="Update" />
    # </form>
    print "Uploading a new version of the plugin"
    zip_file_contents = file_contents(zip_file, "rb")
    post_multipart("anki.ichi2.net", "/file/upload",
        [("type", "plugin"), ("title", release_info["title"]), ("tags", release_info["tags"]), ("description", release_info["description"]), ("id", release_info["id"]), ("submit", "Update")],
        [("file", os.path.basename(zip_file), zip_file_contents)])

def home_path(*components):
    return os.path.join(os.path.expanduser("~"), *components)

def file_contents(path, mode="r"):
    f = open(path)
    try:
        return f.read()
    finally:
        f.close()

if __name__ == "__main__":
    config = eval(file_contents(home_path(".pinyin-toolkit-release")))
    version, date, changelog = list(parse_releases(file_contents(pinyin.utils.toolkitdir("Pinyin Toolkit.txt"))))[0]
    
    print changelog
    print "Press enter to upload version", version, "(" + date + ") ... ",
    
    try:
        sys.stdin.read()
    except KeyboardInterrupt, e:
        sys.exit(1)
    
    description = ["The Pinyin Toolkit adds many useful features to Anki to assist the study of Mandarin. The aim of " +
                   "the project is to greatly enhance the user-experience for students studying the Chinese language.",
                   "",
                   "Homepage: http://batterseapower.github.com/pinyin-toolkit/",
                   "Full feature list: http://wiki.github.com/batterseapower/pinyin-toolkit/features",
                   "Installation instructions: http://wiki.github.com/batterseapower/pinyin-toolkit/installation",
                   "",
                   "Changes in the most recent version:",
                   ""] + changelog
    
    release_info = {
        "id" : "14",
        "title" : "Pinyin Toolkit (" + version + ") - Advanced Mandarin Chinese Support",
        "tags" : "pinyin Mandarin Chinese English dictionary hanzi graph graphs",
        "description" : "\r\n".join(description)
    }
    
    #upload_to_anki_online(config["credentials"], release_info, home_path("Junk", "test-plugin", "test-plugin.zip"))
    pinyin.utils.withtempdir(lambda tempdir: build_release(config["credentials"], release_info, tempdir))
