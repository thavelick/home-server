# Tristan's Home Server

A set of ansible scripts for setting up my home server.

## Services
These scripts set up the following services:
* [Just Bangs](https://github.com/thavelick/just-bangs)
* [Kiwix](https://kiwix.org)
* [Wallabag](https://wallabag.org)

## Upcoming services
* [Miniflux](https://miniflux.net)
* [YouTranscript](https://github.com/thavelick/youtranscript)

## Usage

1. Clone the repository
    ```bash
    git clone https://github.com/thavelick/home-server.git
    cd home-server
    ```
2. Install Ansible
    > See the [Ansible documentation](https://docs.ansible.com/ansible/latest/intro_installation.html)
3. Create an inventory file:
    ```bash
    cat > hosts <<EOF
    [servers]
    my-server.dev.local

    [servers.vars]
    just_bangs_domain=bangs.dev.local
    just_bangs_site_root=/var/www/bangs.dev.local
    kiwix_domain=kiwix.tristanhavelick.com
    kiwix_site_root=/var/www/kiwix.tristanhavelick.com
    wallabag_domain=wallabag.dev.local
    wallabag_site_root=/var/www/wallabag.dev.local
    wallabag_secret="my super secret secret"
    wallabag_server_name="Tristan's Wallabag"
    wallabag_email=tristan@example.com
    wallabag_email_password=a-really-good-password
    wallabag_admin_user=wallabag
    wallabag_admin_password=an-even-better-password
    EOF
    ```
4. Run the playbook:
    ```bash
    ansible-playbook -i hosts playbook.yml
    ```
5. Copy/Upload zim files for kiwix to {{kiwix_site_root}}/data
  * I thought about automating this, but many of these files are huge, making them easier to copy
    locally if you have them, and it's often difficult to determine which is the newest or
    best zim file in an automated fashion