# Tristan's Home Server

A set of ansible scripts for setting up my home server.

## Services
These scripts set up the following services:
* [Just Bangs](https://github.com/thavelick/just-bangs)
* [Kiwix](https://kiwix.org)
* [Miniflux](https://miniflux.net)
* [Wallabag](https://wallabag.org)
* [YouTranscript](https://github.com/thavelick/youtranscript)
* [ChatPad](https://github.com/deiucanta/chatpad)
* [Navidrome](https://www.navidrome.org)
* [SearXNG](https://github.com/searxng/searxng)
* Dynamic DNS with Namecheap

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
    certbot_admin_email=tristan@example.com
    nginx_username=your_username
    nginx_password=your_password
    parent_domain=dev.local
    miniflux_admin_password=good-password
    miniflux_db_user_password=such-a-great-password
    wallabag_secret="my super secret secret"
    wallabag_email=tristan@example.com
    wallabag_email_password=a-really-good-password
    wallabag_admin_user=wallabag
    wallabag_admin_password=an-even-better-password
    dynamicdns_password=aaaaaaaa11111111aaaaaaaa11111111
    EOF
    ```
4. Set up DNS At Name cheap

5. Run the playbook:
    ```bash
    ansible-playbook -i hosts playbook.yml
    ```
6. Copy/Upload zim files for kiwix to {{kiwix_site_root}}/data
  * I thought about automating this, but many of these files are huge, making them easier to copy
    locally if you have them, and it's often difficult to determine which is the newest or
    best zim file in an automated fashion
7. Visit all the sites!
