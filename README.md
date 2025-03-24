# UChiVerify - an indie UChicago Verification Bot
[![Add The Bot](https://img.shields.io/badge/-Add%20The%20Bot-7785cc?style=for-the-badge&link=https%3A%2F%2Fdiscord.com%2Foauth2%2Fauthorize%3Fclient_id%3D1347436993503559691)](https://discord.com/oauth2/authorize?client_id=1347436993503559691) [![Static Badge](https://img.shields.io/badge/-Support%20Server-ffffff?style=for-the-badge&logo=discord&link=https%3A%2F%2Fdiscord.com%2Foauth2%2Fauthorize%3Fclient_id%3D1347436993503559691)](https://discord.gg/syNk2wNp2x) [![portfolio](https://img.shields.io/badge/my_portfolio-000?style=for-the-badge&logoColor=white)](https://dariel.us/) [![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/darielc) [![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/darieltweet)

A bot to authenticate users as UChicago affiliates, made for Transit Enthusiasts RSO and free-to-use to the UChicago community.

## Open Source Disclaimer
Although the code is open source, you won't be able to actually run the bot on your own without University IT sponsorship. UChiVerify runs on a secret key issued by the University to run on their Okta SSO system. If you want to run a similar bot, I reccomend using Google's [OAuth 2.0 API](https://developers.google.com/identity/sign-in/web/sign-in) and filtering only to email addresses ending in uchicago's domain name. The only caveat to this alternative method is that not all University affiliates have a GSuite account.

### Running verification prompts on your own bot
The endpoint for verification is `https://vps.dariel.us/uchiverify/auth/start?guild_id={guild_id}&user_id={user_id}`

You could, in theory, set up your own custom verification prompt where users are given a custom link with prefilled guild and/or user ID parameters. However, in order for role assignment to function properly, **you must have the UChiVerify bot in the server, even if the bot wouldn't be directly interacting with end users.** UChiVerify is the only bot that is able to issue roles *for now*. I'm working on a process to potentially create API keys that control access to the Okta secret keys for other developers to run everything in-house.

## Setting up
### Required Permissions
UChiVerify requires the following permissions:
1. Manage Roles
2. Send Messages
3. Read Message History (and Read Messages in any channel it has a verification prompt)

The link to install the bot should grant these roles automatically, however in the event it doesnt, you can edit the `UChiVerify` role in your server to grant these permissions.

### Adding your verification role
Currently, the bot will only look for a role named `UChicago Verified` to grant to successfully verified users. There is no requirement for this role except that *it must be below `UChiVerify` in the role hierarchy of your server.

The most common use for the Bot by servers is setting a channel that users who do not have `UChicago Verified` can view and those who do have the role cannot. At the same time, the rest of the server is set to the inverse where only verified users can view it. This avoids bots that are unverified from DMing verified server users because they can only access the server’s member list of unverified users.

#### Common Use Template for Verification Channels
<img src="https://i.imgur.com/d3aOKJk.png" width="400" alt="template">

```
# :phoenix: Are you a UChicago affiliate?
This server is open to affiliates of the University of Chicago who hold a CNET login (Alumni, Current Students, Faculty, Post-docs, Researchers, and Hospital Employees)<,and members of certain off campus groups>. 

**To verify your status and be granted access to the rest of the server, click the button below.**

Please DM <server admin> to be granted access if you do not have a CNET account with UChicago, are having trouble verifying, or do not wish to use UChiVerify.
```

### Choosing the channel you want users to verify in
Server administrators can call the bot using the command `/setchannel`, the bot will respond with a verification prompt that users can click on to verify and obtain the `UChicago Verified` role. It is reccomended that you set the channel to view only, but UChiVerify should be allowed to type in the channel.

<img src="https://i.imgur.com/2e7YDcW.gif" width="300" alt="setchannel">

### Troubleshooting
If you need help, visit the [Support Server](https://discord.gg/syNk2wNp2x) or type `/gethelp` in any channel.

## Privacy Policy

This privacy policy applies to the UChiVerify app (hereby referred to as "Application") for web and Discord integration that was created by Dariel Cruz Rodriguez (hereby referred to as "Service Provider") as an Open Source service. This service is intended for use "AS IS".

**Data Collection and Use**

The Application collects information when you use it. This information includes:

*   Your Discord user ID
*   Your UChicago CNET email
*   The Discord server (guild) ID where you are requesting verification

The Service Provider will retain this information and use it solely for the purpose of verifying UChicago affiliates and troubleshooting purposes— should you have issues using the Service. The Service Provider does not collect, store, or process IP addresses, device information, or any location data.

**Third Party Access**

The Service Provider does not sell or share your personal information with third parties, and __**never will**__. Your Discord user ID, CNET email, and guild ID are only used for verification purposes and are stored securely. The Service Provider may disclose your information:

*   as required by law, such as to comply with a subpoena or similar legal process;
*   when the Service Provider believes in good faith that disclosure is necessary to protect their rights, protect your safety or the safety of others, investigate fraud and abuse of the Service, or respond to a government request;

**Data Retention Policy**

The Service Provider will retain this limited information so you don’t need to verify again in the future in the event you are in multiple servers that use UChiVerify, unless you decide to remove it. If you ever want your data deleted, just send an email to hello@dariel.us with the title "UChiVerify - Data Removal Request", and I’ll take care of it as soon as possible.

**Data Security**

The Service Provider is concerned about safeguarding the confidentiality of your information. Physical, electronic, and procedural safeguards are in place to protect the information the Service Provider processes and maintains.

**Changes to This Policy**

This Privacy Policy may be updated from time to time for any reason. Changes will be posted on this page. Continued use of the Application after any modification will constitute acceptance of the updated policy.

If you have any questions regarding privacy while using the Application or about the practices in general, please contact the Service Provider at hello@dariel.us.

**Your Consent**

This privacy policy is effective as of March 23rd, 2025. By using the Application, you consent to the processing of your information as outlined in this Privacy Policy. 
