#!/usr/bin/env python3

### IMPORTS ###
import json
import logging
import os
import subprocess

### GLOBALS ###

### FUNCTIONS ###
def get_requirements_from_payload(payload_json):
    logging.debug("Getting the contents of the requirements.txt file from the payload.")
    logging.debug("  payload_json: %s", payload_json)
    payload_dict = json.loads(payload_json)
    logging.debug("  payload_dict: %s", payload_json)
    pkg_contents = payload_dict['packages']
    logging.debug("  pkg_contents: %s", pkg_contents)
    return pkg_contents

### CLASSES ###
class PythonPackagePuller:
    def __init__(self, login_data, package_line):
        self.logger = logging.getLogger(type(self).__name__)
        self.login_data = login_data
        self.package_line = package_line
        self.to_copy = []
        self.success = False
        self.logger.debug("PythonPackagePuller for package: %s", self.package_line)

    def _install_package(self):
        self.logger.debug("Installing the package")
        # NOTE: A report option was added in pip v 22.2, but our installation isn't using that version currently.
        # NOTE: The image that is used to run this script should be kept in sync with the python version being used for
        #       development and deployment, otherwise there may be potential version misses.
        # pip_cmd = "pip install --disable-pip-version-check --no-color --no-cache --ignore-installed --index-url {} {}".format(
        #     PYPI_INDEX_URL,
        #     self.package_line
        # )
        pip_cmd = "pip download --disable-pip-version-check --no-color --no-cache --index-url {} {}".format(
            self.login_data['pypi_index_url'],
            self.package_line
        )
        pip_output = subprocess.run(pip_cmd.split(' '), stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        self.logger.debug("  pip_output: %s", pip_output)
        # Check for a failed install
        if pip_output.returncode is not 0:
            # NOTE: Since the output from the pip command is captured, it is
            #       possible to parse the output and figure out which dependency
            #       failed.  This isn't required for this example as the failed
            #       curation will be referred to manual review.
            self.logger.warning("Failed to install package: %s", self.package_line)
            self.logger.warning("  Error: %s", pip_output.stderr.decode())
            return
        # Install succeeded, so process the output
        self.success = True
        tmp_output = pip_output.stdout.decode().splitlines()
        self.logger.debug("  pip_output.stdout: %s", tmp_output)
        for item in tmp_output:
            if item[0:13] == "  Downloading":
                tmp_pkg_split = item.split(" ")
                self.logger.debug("  tmp_pkg_split: %s", tmp_pkg_split)
                tmp_pkg_split2 = tmp_pkg_split[3].split('/')
                self.logger.debug("  tmp_pkg_split2: %s", tmp_pkg_split2)
                self.to_copy.append("/".join(tmp_pkg_split2[9:]))
        self.logger.debug("  self._to_copy: %s", self.to_copy)

    def _copy_to_local(self):
        self.logger.debug("Copying package and dependencies to local repo")
        for pkg in self.to_copy:
            self.logger.debug("  pkg: %s", pkg)
            curl_cmd = "curl -f -XPOST -u{}:{} {}/api/copy/{}/{}?to=/{}/{}".format(
                self.login_data['user'],
                self.login_data['apikey'],
                self.login_data['arti_url'],
                "{}-cache".format(self.login_data['remote_repo']),
                pkg,
                self.login_data['local_repo'],
                pkg
            )
            curl_output = subprocess.run(curl_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.debug("  curl_output: %s", curl_output)

    def curate(self):
        self.logger.info("Curating PyPi package: %s", self.package_line)
        # Should figure out how to configure pip to pull from remote repo...
        self._install_package()
        self._copy_to_local()

### MAIN ###
def main():
    # Set up logging
    logging.basicConfig(
        format = "%(asctime)s:%(levelname)s:%(name)s:%(funcName)s: %(message)s",
        level = logging.DEBUG
    )

    logging.info("Preparing Environment")
    tmp_payload_json = os.environ['res_gated_pypi_payload']
    tmp_packages = get_requirements_from_payload(tmp_payload_json)

    tmp_login_data = {}
    tmp_login_data['user'] = os.environ['int_artifactory_user']
    tmp_login_data['apikey'] = os.environ['int_artifactory_apikey']
    tmp_login_data['arti_url'] = os.environ['int_artifactory_url']
    tmp_login_data['local_repo'] = os.environ['local_repo_name']
    tmp_login_data['remote_repo'] = os.environ['remote_repo_name']
    tmp_login_data['pypi_index_url'] = "{}//{}:{}@{}/artifactory/api/pypi/{}/simple".format(
        str(tmp_login_data['arti_url'].split('/')[0]),
        tmp_login_data['user'],
        tmp_login_data['apikey'],
        str(tmp_login_data['arti_url'].split('/')[2]),
        tmp_login_data['remote_repo']
    )

    # NOTE: Currently this script uses the '--no-cache' option for pip, which
    #       forces download of all packages for each run of the pip command.
    #       This could be made a bit more efficient by allowing the cache for
    #       each run, but wiping out the cache at the start of the script.

    logging.info("Curating Packages")
    tmp_pythonpackage_pullers = []
    for tmp_pkg in tmp_packages:
        tmp_pythonpackage_pullers.append(PythonPackagePuller(tmp_login_data, tmp_pkg))
    for tmp_puller in tmp_pythonpackage_pullers:
        tmp_puller.curate()

    # Report Results
    # NOTE: This just prints the results to the log output.  This information
    #       can be gathered and pushed to a webhook on an external system for
    #       reporting, e.g. JIRA or ServiceNow.
    logging.info("Gathering Results")
    tmp_successes = []
    tmp_failures = []
    for tmp_puller in tmp_pythonpackage_pullers:
        if tmp_puller.success:
            tmp_successes.append(tmp_puller.package_line)
        else:
            tmp_failures.append(tmp_puller.package_line)

    if len(tmp_successes) > 0:
        logging.info("Successfully Curated:")
        for item in tmp_successes:
            logging.info("  %s", item)
    if len(tmp_failures) > 0:
        logging.warning("Failed to Curate:")
        for item in tmp_failures:
            logging.warning("  %s", item)

if __name__ == '__main__':
    main()
