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

NEW_SHA_FILE = "new_sha.txt"


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
        ELITEA_SECRET.encode("utf-8"),
        body.encode("utf-8"),
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


    print(
        "Elitea:",
        response.status_code,
        response.text
    )


    response.raise_for_status()



def save_new_sha(sha):

    with open(NEW_SHA_FILE, "w") as file:
        file.write(sha)



def main():

    commit = get_latest_commit()

    latest_sha = commit["sha"]


    print(
        "Latest:",
        latest_sha
    )

    print(
        "Stored:",
        CURRENT_SHA
    )


    if not CURRENT_SHA:

        print(
            "First run"
        )

        save_new_sha(latest_sha)

        return


    if latest_sha != CURRENT_SHA:

        print(
            "New commit detected"
        )


        send_to_elitea(commit)


    else:

        print(
            "No changes"
        )


    save_new_sha(latest_sha)



if __name__ == "__main__":
    main()