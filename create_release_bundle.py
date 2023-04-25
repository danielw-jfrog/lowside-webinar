#!/usr/bin/env python3

### IMPORTS ###
import datetime
import json
import logging
import os
import urllib.request
import urllib.error

### GLOBALS ###
CREATE_BUNDLE_REPOS = [
    "scanned-docker-local",
    "scanned-pypi-local"
]

CREATE_BUNDLE_DATE = datetime.datetime.now() - datetime.timedelta(days=-1)

CREATE_BUNDLE_AQL_FIND = {
    "$and": [
        {
            "$or": [ {"repo":{"$eq": i_repo}} for i_repo in CREATE_BUNDLE_REPOS],
        }, {
            "$or": [
                { "updated": { "$gt": CREATE_BUNDLE_DATE.strftime('%Y-%m-%d %H:%M:00')} }
            ]
        }, {
            "$and": [
                { "name": { "$nmatch": "repository.catalog"} }
            ]
        }
    ]
}

CREATE_BUNDLE_AQL = """items.find({}).include("sha256","updated","modified_by","created","id","original_md5","depth",
"actual_sha1","property.value","modified","property.key","actual_md5","created_by","type","name","repo","original_sha1",
"size","path")
""".format(json.dumps(CREATE_BUNDLE_AQL_FIND))

CREATE_BUNDLE_DICT = {
    "name": "example-bundle",
    "version": CREATE_BUNDLE_DATE.strftime('%Y%m%d.%H%M'),
    "dry_run": False,
    "sign_immediately": True,
    "description": "Example release bundles showing the ability to move curated packages across an air gap.",
    "release_notes": {
        "syntax": "plain_text",
        "content": "A list of packages could be provided here."
    },
    "spec": {
        "queries": [
            {
                "aql": CREATE_BUNDLE_AQL,
                "query_name": "query-1"
            }
        ]
    }
}

### FUNCTIONS ###
def make_api_request(login_data, method, path, data = None):
    """
    Send the request to the JFrog Artifactory API.

    :param dict login_data: Dictionary containing "user", "apikey", and "host" values.
    :param str method: One of "GET", "PUT", or "POST".
    :param str url: URL of the API sans the "host" part.
    :param str data: String containing the data serialized into JSON format.
    :return:
    """
    req_url = "{}{}".format(login_data["host"], path)
    req_headers = {"Content-Type": "application/json"}
    req_data = data.encode("utf-8") if data is not None else None

    logging.debug("req_url: %s", req_url)
    logging.debug("req_headers: %s", req_headers)
    logging.debug("req_data: %s", req_data)

    req_pwmanager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    req_pwmanager.add_password(None, login_data["host"], login_data["user"], login_data["apikey"])
    req_handler = urllib.request.HTTPBasicAuthHandler(req_pwmanager)
    req_opener = urllib.request.build_opener(req_handler)
    urllib.request.install_opener(req_opener)

    request = urllib.request.Request(req_url, data = req_data, headers = req_headers, method = method)
    resp = None
    try:
        with urllib.request.urlopen(request) as response:
            # Check the status and log
            # NOTE: response.status for Python >=3.9, change to response.code if Python <=3.8
            resp = response.read().decode("utf-8")
            logging.debug("  Response Status: %d, Response Body: %s", response.status, resp)
            logging.info("Repository operation successful")
    except urllib.error.HTTPError as ex:
        logging.warning("Error (%d) for repository operation", ex.code)
        logging.debug("  response body: %s", ex.read().decode("utf-8"))
    except urllib.error.URLError as ex:
        logging.error("Request Failed (URLError): %s", ex.reason)
    return resp

### CLASSES ###

### MAIN ###
def main():
    # Set up logging
    logging.basicConfig(
        format = "%(asctime)s:%(levelname)s:%(name)s:%(funcName)s: %(message)s",
        level = logging.DEBUG
    )

    logging.info("Preparing Environment")

    login_data = {}
    login_data['user'] = os.environ['int_distribution_user']
    login_data['apikey'] = os.environ['int_distribution_apikey']
    login_data['dist_url'] = os.environ['int_distribution_url']
    login_data['host'] = login_data['dist_url'][0:-12] # Trim the work "distribution" off the end.
    logging.debug("login_data: %s", login_data)

    logging.debug("CREATE_BUNDLE_REPOS: %s", CREATE_BUNDLE_REPOS)
    logging.debug("CREATE_BUNDLE_DATE: %s", CREATE_BUNDLE_DATE)
    logging.debug("CREATE_BUNDLE_AQL_FIND: %s", CREATE_BUNDLE_AQL_FIND)
    logging.debug("CREATE_BUNDLE_AQL: %s", CREATE_BUNDLE_AQL)
    logging.debug("CREATE_BUNDLE_DICT: %s", CREATE_BUNDLE_DICT)
    logging.debug("REQUEST_JSON: %s", json.dumps(CREATE_BUNDLE_DICT))

    logging.info("Sending the request to create the bundle.")

    req_url = "/api/v1/release_bundle"
    req_data = json.dumps(CREATE_BUNDLE_DICT)
    make_api_request(login_data, 'POST', req_url, req_data)

if __name__ == "__main__":
    main()

