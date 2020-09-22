#!/usr/bin/python3

import os
import requests
import yaml
import re
import sys
import datetime
import click
import hashlib
import subprocess
from .manager import log, handler, action


def config_parser(config_file):
    with open(config_file) as yaml_file:
        try:
            config = yaml.safe_load(yaml_file)
        except Exception as e:
            logger.critical("Config konnte nicht geladen werden")
            logger.debug(e, exc_info=True)
            sys.exit(2)
    return config


def download_and_store(name, url, filename=None):
    try:
        r = requests.get(url, allow_redirects=True)
        if r.status_code != 200:
            logger.error("Download %s fehlgeschlagen: %s", filename, str(r.status_code))
            return
    except Exception as e:
        logger.error("URL: %s konnte nicht heruntergeladen werden", url)
        logger.debug(e, exc_info=True)
        return

    try:
        if filename is None:
            filename = r.url.rsplit('/', 1)[1]
        dest_file = "{0}/{1}/{2}".format(STORAGE_PATH, name, filename)
        open(dest_file, 'wb').write(r.content)
        return dest_file
    except Exception as e:
        logger.error("File: %s konnte nicht gespeichert werden", dest_file)
        logger.debug(e, exc_info=True)
        return


def local_file_valid(name, url, filename=None):
    """
    Checks local file timestamp aginst Last-Modified Header
    :param name: name of the section
    :param url: url to check Last-Modified header
    :param filename: local filename to timestamp
    :return: True if localtimestamp <= remote
    """
    try:
        r = requests.head(url, allow_redirects=True)
        if filename is None:
            if 'content-disposition' in r.headers:
                filename = re.findall("filename=(.+)", r.headers['content-disposition'])
            else:
                filename = r.url.rsplit('/', 1)[1]
    except Exception as e:
        logger.error("URL: %s konnte nicht erreicht werden", url)
        logger.debug(e, exc_info=True)
        return False

    try:
        dest_file = "{0}/{1}/{2}".format(STORAGE_PATH, name, filename)
        if not os.path.isfile(dest_file):
            return False
        if 'Last-Modified' not in r.headers:
            return False
        url_date = datetime.datetime.strptime(r.headers['Last-Modified'], "%a, %d %b %Y %H:%M:%S GMT")
        file_date = datetime.datetime.utcfromtimestamp(os.path.getmtime(dest_file))
        logger.debug("URL_DATE: %s FILE_DATE: %s", str(url_date), str(file_date))
        # Wenn url_date neuer 'größer timestamp' dann download
        if url_date > file_date:
            return False
    except Exception as e:
        logger.debug(e, exc_info=True)
        return False
    return True


def hash_file(file_path, algo, buf_size=4 * 1024**2):
    hasher = hashlib.new(algo)
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()


def check_md5sum(name, checksumUrl):
    sumfile = download_and_store(name, checksumUrl)
    if not sumfile:
        return False
    try:
        subprocess.run(["md5sum", "--check", "--silent", sumfile], cwd=os.path.dirname(sumfile), shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.debug(e, exc_info=True)
        return False
    return True


def verify_hash(file, hash, type="md5"):
    compare_string = '%s  %s' % hash, file
    compare_util = '%ssum' % type
    try:
        subprocess.run(["echo", compare_string, "|", compare_util, "--check"], shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.debug(e, exc_info=True)
        return False
    return True


def get_vscode_extension(name, config):
    outfiles = []
    extensions = config['extensions']
    if isinstance(extensions, str):
        extensions = [extensions, ]
    for extension in extensions:
        try:
            url, extname = handler.vscode_extension_api(extension)
        except Exception as e:
            logger.error("Kann VSCode API nicht erreichen")
            logger.debug(e, exc_info=True)
            return outfiles

        logger.debug("Downloading %s from %s", extname, url)

        if os.path.isfile(STORAGE_PATH + '/' + name + '/' + extname):
            logger.debug("File `%s` ist bereits aktuell", extname)
            continue
        outfiles.append(download_and_store(name, url, filename=extname))
        logger.info("VSCode extions `%s` heruntergeladen", ", ".join(outfiles))
    return outfiles


def get_github_release(name, config):
    outfiles = []
    if "repo" not in config:
        logger.error("Der Eintrag %s hat kein 'repo' gestetzt", name)
        return outfiles

    try:
        #  and config['type'] == 'tag'
        if 'type' in config:
            if 'version' not in config:
                logger.error("Github tag needs a version")
                return outfiles
            url, extname = handler.github_tag_api(name, config, githubtoken=GITHUBTOKEN)
        else:
            url, extname = handler.github_release_api(name, config, githubtoken=GITHUBTOKEN)
    except Exception as e:
        logger.error("HTTP Fehler beim Download: %s", name)
        logger.debug(e, exc_info=True)
        return outfiles

    if os.path.isfile(STORAGE_PATH + '/' + name + '/' + extname) or extname is None:
        logger.debug("File `%s` ist bereits aktuell", extname)
        return outfiles

    outfiles.append(download_and_store(name, url, filename=extname))
    logger.info("Github Release `%s` heruntergeladen", ", ".join(outfiles))
    return outfiles


def get_github_json(name, config):
    outfiles = []
    if "repo" not in config:
        logger.error("Der Eintrag %s hat kein 'repo' gestetzt", name)
        return outfiles

    try:
        version, url, extname = handler.github_json_check(name, config, githubtoken=GITHUBTOKEN)
    except Exception as e:
        logger.error("HTTP Fehler beim Download: %s", name)
        logger.debug(e, exc_info=True)
        return outfiles

    stored_file_path = "{0}/{1}/{2}".format(STORAGE_PATH, name, extname)
    version_file_path = "{0}.version".format(stored_file_path, version)

    if os.path.isfile(stored_file_path):
        if os.path.isfile(version_file_path):
            with open(version_file_path, 'rb') as f:
                stored_version = f.read()
            if stored_version == version:
                logger.debug("File `%s` ist bereits aktuell", extname)
                return outfiles

    with open(version_file_path, 'w') as f:
        f.write(version)
    outfiles.append(download_and_store(name, url, filename=extname))
    logger.info("Github zip `%s` heruntergeladen", ", ".join(outfiles))
    return outfiles


def get_from_handler(name, handlername, config):
    outfiles = []
    try:
        url, extname = getattr(handler, handlername)(name)
    except Exception as e:
        logger.error("HTTP Fehler beim Download: %s", name)
        logger.debug(e, exc_info=True)
        return outfiles

    if os.path.isfile(STORAGE_PATH + '/' + name + '/' + extname) or extname is None:
        logger.debug("File `%s` ist bereits aktuell", extname)
        return outfiles

    outfiles.append(download_and_store(name, url, filename=extname))
    logger.info("File `%s` heruntergeladen", ", ".join(outfiles))
    return outfiles


def get_filename_from_url(url):
    try:
        res = requests.head(url, allow_redirects=True)
    except Exception as e:
        logger.error("Fehler beim zugriff auf : %s", url)
        logger.debug(e, exc_info=True)
        return

    redirected_url = res.url
    uri_filename = redirected_url.rsplit('/', 1)[1]
    filename = uri_filename.rsplit('?', 1)[0]
    return filename


def oneshot_download(url):
    filename = get_filename_from_url(url)
    logger.debug("Starte Download: %s", filename)
    outfile = download_and_store("oneshot", url, filename=filename)
    logger.info("File `%s` heruntergeladen", filename)
    return outfile


def action_handler(filepath):
    if filepath is not None and os.path.isfile(filepath):
        filename = filepath.replace(STORAGE_PATH, '')
        checksum = hash_file(filepath, 'sha1')
        return filename, checksum
    raise Exception('NOFILE')


def get_static_file(name, config):
    outfiles = []
    if "url" not in config:
        logger.error("Der Eintrag %s hat keine 'url' gestetzt", name)
        return outfiles

    urls = config['url']
    if isinstance(urls, str):
        urls = [urls, ]
    logger.debug(urls)

    for url in urls:
        if "filename" in config:
            filename = config['filename']
        else:
            filename = get_filename_from_url(url)

        if local_file_valid(name, url, filename=filename):
            logger.debug("File `%s` ist bereits aktuell", filename)
            continue

        logger.debug("Starte Download: %s", filename)
        outfiles.append(download_and_store(name, url, filename=filename))
        if "sum" in config:
            if not check_md5sum(name, config['sum']):
                logger.error("Der Eintrag %s hat eine invalide checksumme", name)
                outfiles.pop()
                continue

        for hash in ['md5', 'sha256', 'sha512']:
            if hash in config:
                if not verify_hash(name, config[hash], hash):
                    logger.error("Der Eintrag %s hat einen abweichenden %s Hash", name, hash)
                    outfiles.pop()
                    continue

        logger.info("File `%s` heruntergeladen", filename)
    return outfiles


def parallel_worker(name, section):
    logger.debug("Starte section: %s", name)
    os.makedirs(STORAGE_PATH + '/' + name, mode=0o775, exist_ok=True)
    new_files = []
    try:
        for dltype, dlitems in section.items():
            if dltype == 'github_release':
                new_files.extend(get_github_release(name, dlitems))
            elif dltype == 'github_json':
                new_files.extend(get_github_json(name, dlitems))
            elif dltype == 'static_file':
                new_files.extend(get_static_file(name, dlitems))
            elif dltype == 'vscode':
                new_files.extend(get_vscode_extension(name, dlitems))
            elif dltype == 'selenium':
                new_files.extend(handler.selenium_handler(name, dlitems))
            else:
                new_files.extend(get_from_handler(name, dltype, dlitems))
                
    except Exception as e:
        logger.error("Fehler beim verarbeiten der section %s", name)
        logger.debug(e, exc_info=True)
    return new_files


@click.command()
@click.option('-d', '--debug',
              is_flag=True,
              default=False,
              envvar='RD_JOB_LOGLEVEL')
@click.option('--config', 'config_file',
              default='/etc/downloadmanager/config.yaml',
              help="Config File defaults to 'config.yaml'",
              envvar='CONFIG_FILE')
@click.option('--oneshot', 'oneshot',
              help="Oneshot Download specified URL")
@click.option('--githubtoken', 'githubtoken',
              envvar='GITHUBTOKEN',
              help="Github OAuth Token")
@click.option('--trigger', 'trigger',
              type=click.Choice(['artifactory']),
              envvar='TRIGGER',
              help="Action after Download")
@click.option('--storage', 'storage',
              default='mirror',
              envvar='STORAGE',
              help="Cache Storage Path")
def main(config_file, debug, oneshot, githubtoken, trigger, storage):
    """Python Download Manager"""
    global STORAGE_PATH
    global GITHUBTOKEN
    global logger
    STORAGE_PATH = storage
    GITHUBTOKEN = githubtoken
    logger = log.configure_logging(debug)
    config = config_parser(config_file)

    try:
        if config is None:
            logger.info("Das Konfigurationsfile {0} ist leer.".format(config_file))
            sys.exit(3)

        if oneshot is not None:
            # if is_url(oneshot):
            logger.info("Oneshot mode für: {0}".format(oneshot))
            filepath = oneshot_download(oneshot)
            filename, checksum = action_handler(filepath)
            if trigger == 'artifactory':
                action.upload_to_artifactory(filename, filepath, checksum)
                action.cleanup_artifactory(filename)
            return

        # with Pool() as pool:
        #    new_files = pool.starmap(parallel_worker, config.items())
        new_files = []
        for name, item in config.items():
            new_files.append(parallel_worker(name, item))

        if any(isinstance(e, list) for e in new_files):
            flattend_files = [f for e in new_files for f in e]
            new_files = flattend_files

        logger.debug(new_files)
        for filepath in filter(None, new_files):
            filename, checksum = action_handler(filepath)
            if trigger == 'artifactory':
                action.upload_to_artifactory(filename, filepath, checksum)
                action.cleanup_artifactory(filename)

    except Exception as e:
        logger.error("Hups das hätten nicht passiern dürfen")
        logger.debug(e, exc_info=True)
        sys.exit(-1)


if __name__ == "__main__":
    main()
