import os
import json
import hmac
import hashlib
import requests


# GitHub repository to monitor
OWNER = "muk-as"
REPO = "DOTA2_CLIENT"
BRANCH = "master"


# Elitea webhook URL
ELITEA_WEBHOOK = os.environ["ELITEA_WEBHOOK"]

# Elitea webhook secret
ELITEA_SECRET = os.environ["ELITEA_SECRET"]


STATE_FILE = "last_commit.json"



def get_latest_commit():

    url = (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/commits?sha={BRANCH}"
    )

    response = requests.get(url)

    response.raise_for_status()

    commits = response.json()

    return commits[0]



def load_previous_commit():

    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as file:
        data = json.load(file)

    return data.get("sha")



def save_commit(sha):

    with open(STATE_FILE, "w") as file:
        json.dump(
            {
                "sha": sha
            },
            file,
            indent=2
        )



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
        "commit_message": commit["commit"]["message"],
        "author": commit["commit"]["author"]["name"],
        "commit_url": commit["html_url"]
    }


    body = json.dumps(payload)


    signature = create_signature(body)


    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature
    }


    response = requests.post(
        ELITEA_WEBHOOK,
        data=body,
        headers=headers
    )


    print(
        "Elitea response:",
        response.status_code,
        response.text
    )


    response.raise_for_status()



def main():

    print("Checking repository...")

    commit = get_latest_commit()


    current_sha = commit["sha"]

    previous_sha = load_previous_commit()


    print("Current commit:")
    print(current_sha)


    print("Previous commit:")
    print(previous_sha)



    # First run
    if previous_sha is None:

        save_commit(current_sha)

        print(
            "Initial commit saved"
        )

        return



    if current_sha != previous_sha:

        print(
            "New commit detected!"
        )


        send_to_elitea(commit)


        save_commit(current_sha)


    else:

        print(
            "No new commits"
        )



if __name__ == "__main__":
    main()