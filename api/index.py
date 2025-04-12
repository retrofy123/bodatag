import requests
import random
from flask import Flask, jsonify, request

app = Flask(__bodatag__)
title = "10EB89"
secretkey = "8OAWIW6HSTQTRP7X87JF8DW5HUTBMNXB7EBXHHJW3IOU8RNPGU "
coems = {}

def authjh():
    return {"content-type": "application/json", "X-SecretKey": secretkey}

def check_ban_status(playfab_id):
    ban_url = f"https://{title}.playfabapi.com/Server/GetUserBans"
    response = requests.post(
        url=ban_url,
        json={"PlayFabId": playfab_id},
        headers=authjh()
    )
    if response.status_code == 200:
        ban_data = response.json()
        bans = ban_data.get("data", {}).get("Bans", [])
        if bans:
            return True, [{"Reason": ban.get("Reason"), "Active": ban.get("Active")} for ban in bans]
    return False, None

@app.route("/api/PlayFabAuthentication", methods=["POST"])
def PlayFabAuthentication():
    data = request.get_json()
    CustomId = data.get("CustomId", "Null")

    login_request = requests.post(
        url=f"https://{title}.playfabapi.com/Server/LoginWithServerCustomId",
        json={
            "ServerCustomId": CustomId,
            "CreateAccount": True
        },
        headers=authjh()
    )

    if login_request.status_code == 200:
        data = login_request.json().get("data")
        session_ticket = data.get("SessionTicket")
        entity_token = data.get("EntityToken").get("EntityToken")
        playfab_id = data.get("PlayFabId")
        entity_type = data.get("EntityToken").get("Entity").get("Type")
        entity_id = data.get("EntityToken").get("Entity").get("Id")

        is_banned, ban_details = check_ban_status(playfab_id)
        if is_banned:
            return jsonify({
                "Message": "You have been banned by PlayFab",
                "BanDetails": ban_details
            }), 403

        if playfab_id in coems and coems[playfab_id].get("Banned", False):
            return jsonify({
                "Message": "You have been banned by the reference system",
                "BanReason": coems[playfab_id].get("Reason", "No reason provided")
            }), 403

        coems[playfab_id] = {
            "SessionTicket": session_ticket,
            "EntityToken": entity_token,
            "EntityId": entity_id,
            "EntityType": entity_type
        }

        link_response = requests.post(
            url=f"https://{title}.playfabapi.com/Server/LinkServerCustomId",
            json={
                "ForceLink": True,
                "PlayFabId": playfab_id,
                "ServerCustomId": CustomId,
            },
            headers=authjh()
        ).json()

        return jsonify({
            "PlayFabId": playfab_id,
            "SessionTicket": session_ticket,
            "EntityToken": entity_token,
            "EntityId": entity_id,
            "EntityType": entity_type
        }), 200
    else:
        if login_request.status_code == 403:
            ban_info = login_request.json()
            if ban_info.get('errorCode') == 1002:
                ban_message = ban_info.get('errorMessage', "No ban message provided.")
                ban_details = ban_info.get('errorDetails', {})
                ban_expiration_key = next(iter(ban_details.keys()), None)
                ban_expiration_list = ban_details.get(ban_expiration_key, [])
                ban_expiration = ban_expiration_list[0] if len(ban_expiration_list) > 0 else "No expiration date provided."
                return jsonify({
                    'BanMessage': ban_expiration_key,
                    'BanExpirationTime': ban_expiration
                }), 403
            else:
                return jsonify({
                    'Error': 'PlayFab Error',
                    'Message': ban_info.get('errorMessage', 'Forbidden without ban information.')
                }), 403
        else:
            error_info = login_request.json()
            return jsonify({
                'Error': 'PlayFab Error',
                'Message': error_info.get('errorMessage', 'An error occurred.')
            }), login_request.status_code

@app.route("/api/titledata", methods=["POST", "GET"])
def get_title_data():
    title_data_url = f"https://{title}.playfabapi.com/Server/GetTitleData"
    response = requests.post(
        url=title_data_url,
        headers=authjh()
    )
    if response.status_code == 200:
        return jsonify(response.json().get("data", {}).get("Data", {})), 200
    return jsonify({"Error": "Failed to fetch title data"}), response.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=63718)
