#!/usr/bin/env python3

### IMPORTS ###
import datetime
import json
import logging
import os
import subprocess

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

CREATE_BUNDLE_AQL = """
items.find({}).include("sha256","updated","modified_by","created","id","original_md5","depth","actual_sha1",
                       "property.value","modified","property.key","actual_md5","created_by","type","name","repo",
                       "original_sha1","size","path")
""".format(json.dumps(CREATE_BUNDLE_AQL_FIND))

CREATE_BUNDLE_DICT = {
  "name": "example-bundle",
  "version": "",
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

### CLASSES ###

### MAIN ###
def main():
    # Set up logging
    logging.basicConfig(
        format = "%(asctime)s:%(levelname)s:%(name)s:%(funcName)s: %(message)s",
        level = logging.DEBUG
    )

    logging.info("Preparing Environment")

    tmp_login_data = {}
    tmp_login_data['user'] = os.environ['int_artifactory_user']
    tmp_login_data['apikey'] = os.environ['int_artifactory_apikey']
    tmp_login_data['arti_url'] = os.environ['int_artifactory_url']

    logging.debug("CREATE_BUNDLE_REPOS: %s", CREATE_BUNDLE_REPOS)
    logging.debug("CREATE_BUNDLE_DATE: %s", CREATE_BUNDLE_DATE)
    logging.debug("CREATE_BUNDLE_AQL_FIND: %s", CREATE_BUNDLE_AQL_FIND)
    logging.debug("CREATE_BUNDLE_AQL: %s", CREATE_BUNDLE_AQL)
    logging.debug("CREATE_BUNDLE_DICT: %s", CREATE_BUNDLE_DICT)
    logging.debug("REQUEST_JSON: %s", json.dumps(CREATE_BUNDLE_DICT))

if __name__ == "__main__":
    main()

