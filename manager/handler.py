from pyquery import PyQuery as pq
import json
import requests
import re
import logging
import importlib


GITHUB_API = "https://api.github.com/repos"
HASHICORP_URI = "https://releases.hashicorp.com"
VSCODE_MARKETPLACE = "https://marketplace.visualstudio.com"
logger = logging.getLogger('dlmanager')


def versionsplit(version):
    major, minor, micro = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', version).groups()
    return int(major), int(minor), int(micro)


def vscode_extension_api(itemname):
    api_url = "{0}/items?itemName={1}".format(VSCODE_MARKETPLACE, itemname)
    htmldata = pq(url=api_url)
    extensiondatajson = htmldata('script.vss-extension:first').text()    # MAGIC CSS SELECTOR
    extensiondata = json.loads(extensiondatajson)
    publisher = extensiondata['publisher']['publisherName']
    extension_name = extensiondata['extensionName']
    version = extensiondata['versions'][0]['version']
    download_url = "https://{0}.gallery.vsassets.io/_apis/public/gallery/publisher/{0}/extension/{1}/{2}/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage".format(publisher, extension_name, version) # noqa E501
    filename = "{0}-{1}-{2}.vsix".format(publisher, extension_name, version)
    return [download_url, filename]


def github_release_api(name, config, githubtoken=None):
    api_url = '{0}/{1}/releases/{2}'.format(GITHUB_API, config['repo'], config.get("version", "latest"))
    if githubtoken is not None:
        authheader = {'Authorization': 'token {0}'.format(githubtoken)}
        r = requests.get(api_url, headers=authheader)
    else:
        r = requests.get(api_url)
    json_r = r.json()

    if 'assets' in config:
        regex = re.compile(config['assets'])
        for a in json_r['assets']:
            if regex.fullmatch(a['name']):
                downloadname = a['name']
                return [a['browser_download_url'], downloadname]
    downloadname = '{0}-{1}.tar.gz'.format(name, json_r['tag_name'])
    return [json_r['tarball_url'], downloadname]


def hashicorp_release_api(name, product):
    api_url = '{0}/{1}'.format(HASHICORP_URI, product)
    r = requests.get(api_url)
    pqdata = pq(r.text)
    hrefs = [i.attr('href') for i in pqdata('a').items()]
    regex = re.compile(r"/{0}/(\d+\.\d+\.\d+)/".format(product))
    versions = [regex.fullmatch(c).group(1) for c in hrefs if regex.fullmatch(c)]
    latestversion = max(versions, key=versionsplit)
    logger.debug("Neuerste Version: {0}".format(latestversion))
    downloadname = '{0}_{1}_linux_amd64.zip'.format(product, latestversion)
    dlurl = '{0}/{1}/{2}/{3}'.format(HASHICORP_URI, product, latestversion, downloadname)
    return [dlurl, downloadname]


def github_tag_api(name, config, githubtoken=None):
    api_url = '{0}/{1}/tags'.format(GITHUB_API, config['repo'])
    if githubtoken is not None:
        authheader = {'Authorization': 'token {0}'.format(githubtoken)}
        r = requests.get(api_url, headers=authheader)
    else:
        r = requests.get(api_url)
    r = requests.get(api_url)
    json_r = r.json()

    for tag in json_r:
        if config['version'] == tag['name']:
            downloadname = '{0}-{1}.tar.gz'.format(name, tag['name'])
            return [tag['tarball_url'], downloadname]


def selenium_handler(name, config):
    # TODO: IMPLEMENT
    return []
    try:
        logger.debug("Starte selenium driver: %s", name)
        handler_module = importlib.import_module(config['handler'])
        filename = handler_module.main()
        return [filename]
    except Exception as e:
        logger.error("Selenium Driver failed")
        logger.debug(e, exc_info=True)
