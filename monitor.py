import os
import json
import hmac
import hashlib
import requests


OWNER = "muk-as"
REPO = "DOTA2_CLIENT"
BRANCH = "master"


ELITEA_WEBHOOK = os.environ["ELITEA_WEBHOOK"]
ELITEA_SECRET = os.environ["ELITEA_SECRET"]

CURRENT_SHA = os.environ.get("LAST_COMMIT_SHA", "")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

VARIABLE_NAME = "LAST_COMMIT_SHA"



def get_latest_commit():

    url = (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/commits?sha={BRANCH}"
    )


    response = requests.get(url)

    response.raise_for_status()

    return response.json()[0]



def create_signature(body):

    signature = hmac.new(
        ELITEA_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"sha256={signature}"



def send_to_elitea(commit):

    payload = {
        "repository": f"{OWNER}/{REPO}",
        "branch": BRANCH,
        "commit_sha": commit["sha"],
        "message": commit["commit"]["message"],
        "author": commit["commit"]["author"]["name"],
        "url": commit["html_url"]
    }


    body = json.dumps(payload)


    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": create_signature(body)
    }


    response = requests.post(
        ELITEA_WEBHOOK,
        data=body,
        headers=headers
    )


    print(response.status_code)
    print(response.text)


    response.raise_for_status()



def update_variable(new_sha):

    url = (
        f"https://api.github.com/repos/"
        f"{os.environ['GITHUB_REPOSITORY']}"
        f"/actions/variables/{VARIABLE_NAME}"
    )


    headers = {
        "Authorization":
            f"Bearer {GITHUB_TOKEN}",

        "Accept":
            "application/vnd.github+json"
    }


    body = {
        "name": VARIABLE_NAME,
        "value": new_sha
    }


    response = requests.patch(
        url,
        headers=headers,
        json=body
    )


    response.raise_for_status()



def main():

    latest = get_latest_commit()

    latest_sha = latest["sha"]


    print(
        "Latest:",
        latest_sha
    )

    print(
        "Stored:",
        CURRENT_SHA
    )


    # first run
    if not CURRENT_SHA:

        print(
            "First run. Saving SHA."
        )

        update_variable(latest_sha)

        return



    if latest_sha != CURRENT_SHA:

        print(
            "New commit detected!"
        )


        send_to_elitea(latest)


        update_variable(latest_sha)


    else:

        print(
            "No new commits."
        )



if __name__ == "__main__":
    main()