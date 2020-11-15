#!/usr/bin/env python3
# Longusta (local bongusta??)
# Let's you save your favorite phlogs on local disk for later offline reading.
# And preservation! :3
# 2020, d34dm8|hexed (spiderierusalim@mail.bg)
# Parsing and some other parts are copied from VF-1 goher client(1)
# [1](https://github.com/solderpunk/VF-1/)

import urllib.parse

# Lightweight representation of an item in Gopherspace
GopherItem = collections.namedtuple("GopherItem",
        ("host", "port", "path", "itemtype", "name"))

def url_to_gopheritem(url):
    # urllibparse.urlparse can handle IPv6 addresses, but only if they
    # are formatted very carefully, in a way that users almost
    # certainly won't expect.  So, catch them early and try to fix
    # them...
    if url.count(":") > 2: # Best way to detect them?
        url = fix_ipv6_url(url)
    # Prepend a gopher schema if none given
    if "://" not in url:
        url = "gopher://" + url
    u = urllib.parse.urlparse(url)
    # https://tools.ietf.org/html/rfc4266#section-2.1
    path = u.path
    if u.path and u.path[0] == '/' and len(u.path) > 1:
        itemtype = u.path[1]
        path = u.path[2:]
    else:
        # Use item type 1 for top-level selector
        itemtype = 1
    return GopherItem(u.hostname, u.port or 70, path,
                      str(itemtype), "")

def fix_ipv6_url(url):
    # If there's a pair of []s in there, it's probably fine as is.
    if "[" in url and "]" in url:
        return url
    # Easiest case is a raw address, no schema, no path.
    # Just wrap it in square brackets and whack a slash on the end
    if "/" not in url:
        return "[" + url + "]/"
    # Now the trickier cases...
    if "://" in url:
        schema, schemaless = url.split("://")
    else:
        schema, schemaless = None, url
    if "/" in schemaless:
        netloc, rest = schemaless.split("/",1)
        schemaless = "[" + netloc + "]" + "/" + rest
    if schema:
        return schema + "://" + schemaless
    return schemaless

def gopheritem_to_url(gi):
    if gi and gi.host:
        return ("gopher://%s:%d/%s%s" % (
            gi.host, int(gi.port),
            gi.itemtype, gi.path))
    elif gi:
        return gi.path
    else:
        return ""

def gopheritem_from_line(line):
    # Split on tabs.  Strip final element after splitting,
    # since if we split first we loose empty elements.
    parts = line.split("\t")
    parts[-1] = parts[-1].strip()
    # Discard Gopher+ noise
    if parts[-1] == "+":
        parts = parts[:-1]
    # Attempt to assign variables.  This may fail.
    # It's up to the caller to catch the Exception.
    name, path, host, port = parts
    itemtype = name[0]
    name = name[1:]
    port = int(port)
    # Handle the h-type URL: hack for secure links
    if itemtype == "h" and path.startswith("URL:gopher"):
        url = path[4:]
        return url_to_gopheritem(url)
    return GopherItem(host, port, path, itemtype, name)

def gopheritem_to_line(gi, name=""):
    name = ((name or gi.name) or gopheritem_to_url(gi))
    # Prepend itemtype to name
    name = str(gi.itemtype) + name
    path = gi.path
    return "\t".join((name, path, gi.host or "", str(gi.port))) + "\n"

# Cheap and cheerful URL detector
def looks_like_url(word):
    return "." in word and ("gopher://" in word or "gophers://" in word)

def extract_url(word):
    # Given a word that probably contains a URL, extract that URL from
    # with sensible surrounding punctuation.
    for start, end in (("<",">"), ('[',']'), ("(",")"), ("'","'"), ('"','"')):
        if word[0] == start and end in word:
            return word[1:word.rfind(end)]
    if word.endswith("."):
        return word[:-1]
    else:
        return word

