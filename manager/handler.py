from pyquery import PyQuery as pq
import json
import requests
import re
import logging
import importlib
import configparser


GITHUB_API = "https://api.github.com/repos"
GITHUB_RAW_CONTENT = "https://raw.githubusercontent.com"
HASHICORP_URI = "https://releases.hashicorp.com"
PYTHON_URI = "https://www.python.org"
VSCODE_MARKETPLACE = "https://marketplace.visualstudio.com"
TRENDMICRO_BASE = "http://smln-p.activeupdate.trendmicro.com/activeupdate"
TOMCAT_REPO = 'https://mirror.joestr.priv.at/pub/apache/tomcat/tomcat-9'
QGIS_REPO = 'https://plugins.qgis.org/plugins'

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


def github_api_requester(url, githubtoken=None):
    if githubtoken is not None:
        authheader = {'Authorization': 'token {0}'.format(githubtoken)}
        r = requests.get(url, headers=authheader)
    else:
        r = requests.get(url)
    json_r = r.json()
    logger.debug("Aufruf: {0}, Returned {1}".format(r.url, r.status_code))
    return json_r


def github_release_api(name, config, githubtoken=None):
    api_url = '{0}/{1}/releases/{2}'.format(GITHUB_API, config['repo'], config.get("version", "latest"))
    json_r = github_api_requester(api_url, githubtoken)

    if 'assets' in config:
        regex = re.compile(config['assets'])
        for a in json_r['assets']:
            if regex.fullmatch(a['name']):
                downloadname = a['name']
                return [a['browser_download_url'], downloadname]
    downloadname = '{0}-{1}.tar.gz'.format(name, json_r['tag_name'])
    return [json_r['tarball_url'], downloadname]


def github_tag_api(name, config, githubtoken=None):
    api_url = '{0}/{1}/tags'.format(GITHUB_API, config['repo'])
    json_r = github_api_requester(api_url, githubtoken)

    for tag in json_r:
        if config['version'] == tag['name']:
            downloadname = '{0}-{1}.tar.gz'.format(name, tag['name'])
            return [tag['tarball_url'], downloadname]


def github_json_check(name, config, githubtoken=None):
    branch = config['branch'] if 'branch' in config else 'master'
    json_file = config['file'] if 'file' in config else 'package.json'
    api_url = '{0}/{1}/{2}/{3}'.format(GITHUB_API, config['repo'], branch, json_file)
    json_r = github_api_requester(api_url, githubtoken)

    if 'version' in json_r:
        downloadurl = 'https://github.com/{0}/archive/{1}.zip'.format(config['repo'], branch)
        downloadname = '{0}-{1}.zip'.format(config['repo'], branch)
        return [json_r['version'], downloadurl, downloadname]
    else:
        raise KeyError("No 'version' key in: " + json_file)


def trendmicro(name):
    ini_url = '{0}/server.ini'.format(TRENDMICRO_BASE)
    r = requests.get(ini_url)
    server_ini = r.text
    config = configparser.ConfigParser()
    config.read_string(server_ini)
    path_vsapi = config['PATTERN']['Path_VSAPI']
    pattern = path_vsapi.split(",")[0]
    downloadname = pattern.split("/")[1]
    dlurl = '{0}/{1}'.format(TRENDMICRO_BASE, pattern)

    return [dlurl, downloadname]


def hashicorp(name, product):
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


def python(name):
    downloadname = "python.exe"
    downloads_url = "{0}/{1}/".format(PYTHON_URI, 'downloads')
    htmldata = pq(url=downloads_url)
    versionbutton = htmldata('div.download-os-windows > p > a').text()
    version = versionbutton.split(" ")[-1]
    binary_url = "{0}/ftp/python/{1}/python-{1}-amd64.exe".format(PYTHON_URI, version)

    return [binary_url, downloadname]


def geoserver(name):
    version_url = "https://raw.githubusercontent.com/geoserver/geoserver.github.io/master/release/stable/index.html"
    r = requests.get(version_url)
    for line in r.text.split("\n"):
        if line.startswith('version:'):
            version = line.split(" ")[1]
    binary_url = "https://sourceforge.net/projects/geoserver/files/GeoServer/{0}/geoserver-{0}-war.zip".format(version)
    downloadname = "geoserver-{0}-war.zip".format(version)

    return [binary_url, downloadname]


def tomcat(name):
    page = requests.get(TOMCAT_REPO).text
    pqdata = pq(page)
    hrefs = [node.attr('href') for node in pqdata('a').items() if node.attr('href').startswith('v9')]
    versions = [version[1:-1] for version in hrefs]
    latest = max(versions, key=versionsplit)
    binary_url = "{0}/v{1}/bin/apache-tomcat-{1}.tar.gz".format(TOMCAT_REPO, latest)
    downloadname = "tomcat-{0}.tar.gz".format(latest)

    return [binary_url, downloadname]


def get_qgis_plugin(plugin):
    page = requests.get("{0}/{1}".format(QGIS_REPO, plugin)).text
    pqdata = pq(page)
    version = [node.next().find('a').text() for node in pqdata('dt').items() if node.text().startswith('Latest stable version')][0]
    binary_url = "{0}/{1}/version/{2}/download/".format(QGIS_REPO, plugin, version)
    downloadname = "{0}-{1}.zip".format(plugin, version)
    return [binary_url, downloadname]


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
