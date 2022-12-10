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
## 4. **Sales Price Update**
- ***Sales Price Update report*** - a report showing all the changes on sales price of a product made different users
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
