# Tristan's Home Server

A set of ansible scripts for setting up my home server.

## Services
These scripts set up the following services:
* [Wallabag](https://wallabag.org)

## Upcoming services
* [Miniflux](https://miniflux.net)
* [Kiwix](https://kiwix.org)
* [Just Bangs](https://github.com/thavelick/just-bangs)
* [YouTranscript](https://github.com/thavelick/youtranscript)

## Other Todo:
* Add SSL support

## Usage

1. Clone the repository
    ```bash
    git clone https://github.com/thavelick/home-server.git
    cd home-server
    ```
2. Install Ansible
    > See the [Ansible documentation](https://docs.ansible.com/ansible/latest/intro_installation.html)
3. Install Vagrant
    > See the [Vagrant documentation](https://www.vagrantup.com/docs/installation)
4. Create an inventory file:
    ```bash
    cat > hosts <<EOF
    [servers]
    my-server.dev.local

    [servers.vars]
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
5. Run the playbook:
    ```bash
    ansible-playbook -i hosts playbook.yml
    ```
