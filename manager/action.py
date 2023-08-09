import logging
import json
import re
import subprocess


logger = logging.getLogger('dlmanager')
versionsplit = re.compile(r'[-_]v?((?:\.?\d)+)')


def upload_to_artifactory(filename, filepath, checksum):
    """
    Upload File to Artifactory

    :param filename: name of file to upload
    :param filepath: abolute filepath of file to upload
    :param checksum: checksum of the file
    :returns: True if successful False if not
    """
    try:
        logger.debug("Uploading %s with Checksum %s to Artifactory", filename, checksum)
        command = "jfcli rt u {0} devtools-upload/{1}".format(filepath, filename)
        subprocess.check_output([command], shell=True)
    except Exception as e:
        logger.debug(e, exc_info=True)
        return False
    return True


def cleanup_artifactory(filename):
    """
    Cleanup old Versions in Artifactory

    :param filename: name most recent file
    :returns: True if successful False if not
    """
    name_parts = re.split(versionsplit, filename, maxsplit=1)
    name = name_parts[0]
    if len(name_parts) <= 1:
        logger.debug("Keine Version gefunden breche Cleanup ab")
        return True
    version = name_parts[1]
    searchcommand = "jfcli rt s devtools-upload{0}*".format(name)
    try:
        jsonresult = subprocess.check_output([searchcommand], shell=True)
    except subprocess.CalledProcessError as e:
        logger.debug(e, exc_info=True)
        return False

    if jsonresult is not None:
        resultarray = json.loads(jsonresult)

    for path in resultarray:
        # print(path['path'].split('1', 1)[0])
        result_parts = re.split(versionsplit, path['path'], maxsplit=1)
        resultname = result_parts[0]
        resultversion = result_parts[1]
        logger.debug(f"Aktuelle Version: {version} Gefundene Version: {resultversion}")
        if version != resultversion:
            logger.debug("Will Delete Version: {0} Of the Artifact: {1}".format(resultversion, resultname))
            deletecommand = "jfcli rt del --quiet {0}".format(path['path'])
            try:
                subprocess.run([deletecommand], shell=True)
            except subprocess.CalledProcessError as e:
                logger.debug(e, exc_info=True)
                return False

    return True
