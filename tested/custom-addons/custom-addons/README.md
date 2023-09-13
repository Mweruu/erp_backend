# K_PartnerFleet Odoo extension module

## This module modifies:
## 1. **Fleet**
Added fields:
- ***partner_id*** - partner/customer whose vehicle belongs to
- ***tonnage***- max luggage weight a vehicle should carry

In the main view, the fields are displayed after **License plate**

## 2. **Partner/Customer**
Added fields:
- ***vehicles*** - List of all vehicles in fleet, that belong to current customer. One can insert a new vehicle by clicking ***Add a Line***

___
## 3. **POS and Sales Reports**
- ***POS Difference report*** - a report for all items sold in POS module at a price different from the fixed price
- ***Sales Difference report*** - a report for all items sold in sales module at a price different from the fixed price

- ***Sales Difference report*** - a report for all items returned in POS module
___


### installing wkhtmltox
To generate PDF reports, a module wkhtmltox needs to be installed. Use the commands:

> cd ~
>
> wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
>
>tar xvf wkhtmltox*.tar.xz
>
>sudo mv wkhtmltox/bin/wkhtmlto* /usr/bin
>
>sudo apt-get install -y openssl build-essential libssl-dev libxrender-dev git-core libx11-dev libxext-dev libfontconfig1-dev libfreetype6-dev fontconfig



## Mail Server Configuration Using App passwords in Odoo 15
1. Sign in to your Google Account
2. After the login process, go through the  Account settings? Security?App 	    	 Passwords.
3. Choose the app and the device for which you wish to create the app password.

4. Then, click on Generate and copy the password generated.

Now configure the mail server in Odoo using this password.
Only the admin user should be used to log in because they have access to all settings and configurations.


## **ODOO OUTGOING MAIL SERVER CONFIGURATION**
To configure outgoing mail servers, follow these breadcrumbs: **Settings ? Technical ?Email? outgoing mail servers.**

You will receive a form and you should provide the following details:
- SMTP Server: smtp.gmail.com
- SMTP port:The server's port(465)
- Connection Security: SSL/TLS
- Username: Your mail account
- Password:  The  newly created app  password
- Priority: The lower the number higher the priority

	
You can use the test connection smart button in the window to check the connectivity. A connection success complete message will also be sent to you if the testing is successful.



## ODOO INCOMING MAIL SERVER CONFIGURATION
Follow these breadcrumbs to obtain the setup window for incoming email:Settings - **Technical - Email - Incoming Mail Servers**

You will receive a form, and you should provide the following details:
- Server Type: IMAP Server
- Server name: The server's name. (imap.gmail.com)
- Port: The server's port(993)
- SSL/TLS:  Check this to encrypt messages
- Username: Your email address
- Password: The  newly created app  password