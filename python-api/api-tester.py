import httpx
import sys
from datetime import UTC, datetime, timedelta
import questionary
import click


def login(client):
    username = questionary.text(
        "Enter your username", default="kent@kentfriesen.com"
    ).unsafe_ask()
    password = questionary.password("Enter your password").unsafe_ask()

    response = client.post("/login", data={"username": username, "password": password})

    return response.json()


def query(client: httpx.Client, credentials):
    url = questionary.text("Query: ").unsafe_ask()

    parts = url.split(" ")
    if len(parts) == 0:
        print("Please enter something")
        return
    if len(parts) == 1:
        method = "GET"
        others = parts
    else:
        method = parts[0]
        others = parts[1:]

    response = client.request(
        method,
        others[0],
        headers={"Authorization": f"Bearer {credentials['access_token']}"},
    )

    try:
        print(response.json())
    except Exception:
        print("Error occurred. Here's the text")
        print(response.text)


@click.command("give-subscriptions")
@click.argument("base_url")
def give_subscriptions(base_url):
    with httpx.Client(base_url=base_url) as client:
        while not (credentials := login(client)):
            print("Login failed")

        while True:
            query(client, credentials)


if __name__ == "__main__":
    give_subscriptions()
