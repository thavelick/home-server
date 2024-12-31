# Tristan's Home Server

A set of ansible scripts for setting up my home server.

## Services
These scripts set up the following services:
* [ChatPad](https://github.com/deiucanta/chatpad)
* [Jellyfin](https://jellyfin.org)
* [Just Bangs](https://github.com/thavelick/just-bangs)
* [Kiwix](https://kiwix.org)
* [Miniflux](https://miniflux.net)
* [Nextcloud](https://nextcloud.com)
* [OnlyOffice](https://www.onlyoffice.com)
* [SearXNG](https://github.com/searxng/searxng)
    * With [Just Auth](https://github.com/thavelick/just-auth) for authentication
* [TubeSync](https://github.com/meeb/tubesync)
* [YouTranscript](https://github.com/thavelick/youtranscript)
* [Transmission + OpenVPN](https://github.com/haugene/docker-transmission-openvpn)
* [Wallabag](https://wallabag.org)
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
    dynamicdns_password=aaaaaaaa11111111aaaaaaaa11111111
    nextcloud_admin_user=your-hidden-password
    local_network=192.168.1.0/16
    marginalia_api_key=your_api_key
    miniflux_admin_password=good-password
    miniflux_db_user_password=such-a-great-password
    onlyoffice_jwt_secret=something-really-secret
    openvpn_provider=your-provider
    openvpn_config=uk_london
    openvpn_username=p83748378
    openvpn_password=ptrlkn1nt
    parent_domain=dev.local
    wallabag_secret="my super secret secret"
    wallabag_email=tristan@example.com
    wallabag_email_password=a-really-good-password
    wallabag_admin_user=wallabag
    wallabag_admin_password=an-even-better-password
    searxng_secret_key=another-secret-key
    searxng_just_auth_password="choose a password for searxng"
    searxng_just_auth_salt="just a random string"
    EOF
    ```
4. Set up DNS At Name cheap
5. Install Ansible Dependencies
    ```bash
    ansible-galaxy install -r requirements.yml
    ```
6. Run the playbook:
    ```bash
    ansible-playbook -i hosts playbook.yml
    ```
7. Copy/Upload zim files for kiwix to {{kiwix_site_root}}/data
  * I thought about automating this, but many of these files are huge, making them easier to copy
    locally if you have them, and it's often difficult to determine which is the newest or
    best zim file in an automated fashion
8. Visit all the sites!
