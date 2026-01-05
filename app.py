import os
import logging
import csv
from datetime import datetime
import urllib.parse

import requests
from flask import Flask, session, request, redirect, render_template_string, render_template
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  # Secret key for session cookies

# Okta OIDC configuration
OKTA_DOMAIN = os.getenv("OKTA_DOMAIN")            # e.g. "your-okta-domain.okta.com"
OKTA_CLIENT_ID = os.getenv("OKTA_CLIENT_ID")      # Okta OIDC app client ID
OKTA_CLIENT_SECRET = os.getenv("OKTA_CLIENT_SECRET")  # Okta OIDC app client secret
OKTA_ISSUER = "https://uchicago.okta.com"

# OAuth endpoints for Okta (using the issuer URL)
AUTHORIZATION_URL = f"{OKTA_ISSUER}/oauth2/v1/authorize"
TOKEN_URL = f"{OKTA_ISSUER}/oauth2/v1/token"
USERINFO_URL = f"{OKTA_ISSUER}/oauth2/v1/userinfo"

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("web.log"), logging.StreamHandler()]
)
logger = app.logger  # Flask's logger (which will use our logging config)

@app.route('/uchiverify/auth/start')
def start_auth():
    """Begin the verification by redirecting the user to Okta for authentication."""
    guild_id = request.args.get('guild_id')
    user_id = request.args.get('user_id')
    if not guild_id or not user_id:
        return "Missing guild_id or user_id", 400
    
    # Store guild and user in session for use after authentication
    session['guild_id'] = guild_id
    session['user_id'] = user_id

    # Generate a random state string for CSRF protection
    state = os.urandom(16).hex()
    session['state'] = state

    # Build the Okta authorization URL with required params
    params = {
        "client_id": OKTA_CLIENT_ID,
        "redirect_uri": "https://vps.dariel.us/auth/callback",
        "response_type": "code",
        "scope": "openid email profile groups",   # request OIDC scopes
        "state": state
    }
    
    auth_url = f"{AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"
    logger.info(f"Initiating Okta OIDC login for Discord user {user_id} (guild {guild_id})")
    return redirect(auth_url)

@app.route('/auth/callback')
def auth_callback():
    """Okta redirects here after login. This route processes the OIDC response."""
    error = request.args.get('error')
    if error:
        # Handle error from Okta (e.g., user denied access)
        logger.warning(f"Okta returned an error: {error}")
        return render_template("verificationfailed.html", error=error)
    code = request.args.get('code')
    state = request.args.get('state')
    # Basic validation of state and presence of code
    if not code or not state or 'state' not in session or state != session['state']:
        logger.error("OIDC state mismatch or missing code.")
        return render_template("verificationfailed.html", error="OIDC state mismatch or missing code.")
    guild_id = session.get('guild_id')
    user_id = session.get('user_id')
    # Exchange authorization code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://vps.dariel.us/auth/callback",
        "client_id": OKTA_CLIENT_ID,
        "client_secret": OKTA_CLIENT_SECRET
    }
    token_res = requests.post(TOKEN_URL, data=token_data)
    if token_res.status_code != 200:
        logger.error(f"Token exchange failed: {token_res.status_code} - {token_res.text}")
        return render_template("verificationfailed.html", error="Could not retrieve authentication token.")
    tokens = token_res.json()
    access_token = tokens.get("access_token")

    # Use the access token to get the user's info
    userinfo_res = requests.get(USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
    if userinfo_res.status_code != 200:
        logger.error(f"Userinfo request failed: {userinfo_res.status_code} - {userinfo_res.text}")
        return render_template("verificationfailed.html", error="Could not retrieve user information.")
    profile = userinfo_res.json()
    email = profile.get("email")
    if not email:
        logger.error("No email found in OIDC profile!")
        return render_template("verificationfailed.html", error="Your email could not be obtained.")
    logger.info(f"Verified Discord user {user_id}, guild {guild_id}: {profile}")
    # Assign the "UChicago Verified" role in Discord via Bot API
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    if bot_token:
        headers = {"Authorization": f"Bot {bot_token}"}
        # Ensure the role exists
        role_id = None
        roles_res = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}/roles", headers=headers)
        if roles_res.status_code == 200:
            for role in roles_res.json():
                if role["name"] == "UChicago Verified":
                    role_id = role["id"]
                    break
        if role_id is None:
            # Create the role (with default permissions)
            new_role = {"name": "UChicago Verified", "mentionable": False}
            create_res = requests.post(f"https://discord.com/api/v10/guilds/{guild_id}/roles",
                                       json=new_role, headers=headers)
            if create_res.status_code in (200, 201):
                role_id = create_res.json().get("id")
                logger.info(f"Created 'UChicago Verified' role in guild {guild_id}")
            else:
                logger.error(f"Failed to create role: {create_res.status_code} - {create_res.text}")
        # Assign role to the user
        if role_id:
            assign_res = requests.put(f"https://discord.com/api/v10/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
                                      headers=headers)
            if assign_res.status_code in (200, 204):
                logger.info(f"Assigned 'UChicago Verified' role to user {user_id} in guild {guild_id}")
            else:
                logger.error(f"Failed to assign role: {assign_res.status_code} - {assign_res.text}")
    else:
        logger.warning("Discord bot token not provided to Flask app; skipping role assignment.")
    # Display a success message to the user
    return render_template("verificationsuccess.html")

if __name__ == "__main__":
    # Run the Flask app (production deployments will use gunicorn + Nginx)
    app.run(host="127.0.0.1", port=5000)