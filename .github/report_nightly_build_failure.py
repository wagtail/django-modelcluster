"""
Called by GitHub Action when the nightly build fails.

This reports an error to the #nightly-build-failures Slack channel.
"""

import os

import requests

if "SLACK_WEBHOOK_URL" in os.environ:
    # https://docs.github.com/en/free-pro-team@latest/actions/reference/environment-variables#default-environment-variables
    repository = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ["GITHUB_RUN_ID"]
    url = f"https://github.com/{repository}/actions/runs/{run_id}"

    print("Reporting to #nightly-build-failures slack channel")  # noqa: T201
    response = requests.post(
        os.environ["SLACK_WEBHOOK_URL"],
        json={
            "text": f"A Nightly build failed. See {url}",
        },
    )

    print(f"Slack responded with: {response}")  # noqa: T201

else:
    print(  # noqa: T201
        "Unable to report to #nightly-build-failures slack channel because SLACK_WEBHOOK_URL is not set"
    )
