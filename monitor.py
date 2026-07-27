import os
import json
import requests


# Repository to monitor
OWNER = "muk-as"
REPO = "DOTA2_CLIENT"
BRANCH = "master"


# Elitea webhook
ELITEA_WEBHOOK = os.environ.get("ELITEA_WEBHOOK")


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
            file
        )


def send_to_elitea(commit):

    payload = {
        "repository": f"{OWNER}/{REPO}",
        "branch": BRANCH,
        "commit_sha": commit["sha"],
        "message": commit["commit"]["message"],
        "author": commit["commit"]["author"]["name"],
        "url": commit["html_url"]
    }


    response = requests.post(
        ELITEA_WEBHOOK,
        json=payload
    )


    response.raise_for_status()

    print("Elitea triggered")



def main():

    commit = get_latest_commit()

    current_sha = commit["sha"]

    old_sha = load_previous_commit()


    print("Current:", current_sha)
    print("Previous:", old_sha)


    # first run
    if old_sha is None:

        save_commit(current_sha)

        print(
            "Initial commit saved"
        )

        return



    if current_sha != old_sha:

        print(
            "New commit detected!"
        )


        send_to_elitea(commit)


        save_commit(current_sha)


    else:

        print(
            "No changes"
        )



if __name__ == "__main__":
    main()