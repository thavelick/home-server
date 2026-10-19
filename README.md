# Tristan's Home Server

A set of ansible scripts for setting up my home server.

## Services
These scripts set up the following services:
* [Ampcast](https://github.com/rekkyrosso/ampcast)
* [fmp4-demux-proxy](https://github.com/jeremy-albinet/Stitch-Revitalized-For-Roku/tree/main/fmp4-demux-proxy) for watching Twitch on a Roku
* [Jellyfin](https://jellyfin.org)
* [Just Bangs](https://github.com/thavelick/just-bangs)
* [Kiwix](https://kiwix.org)
* Links: personal short links (links.example.com/slug), behind [Just Auth](https://github.com/thavelick/just-auth)
* [Miniflux](https://miniflux.net)
* [Nextcloud](https://nextcloud.com)
* [SearXNG](https://github.com/searxng/searxng)
    * With [Just Auth](https://github.com/thavelick/just-auth) for authentication
* [TubeSync](https://github.com/meeb/tubesync)
* [Transmission + OpenVPN](https://github.com/haugene/docker-transmission-openvpn)
* [Wallabag](https://wallabag.org)
* [Webhook.site](https://github.com/webhooksite/webhook.site)
* [WireGuard](https://www.wireguard.com) for remote access to the server and studio
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
    links_just_auth_password="choose a password for links"
    links_just_auth_salt="another random string"
    google_accounts={"work": "you@work.com", "personal": "you@gmail.com"}
    home_assistant_google_service_account_private_key="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
    home_assistant_google_service_account_private_key_id=your_private_key_id
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

## Watching Twitch on a Roku

Twitch Enhanced Broadcasting streams bundle audio and video into a single fMP4
rendition. Roku's player expects one elementary stream per rendition, so those
streams fail with error 970 or play with no audio. The `fmp4_demux_proxy` role
runs a proxy that splits them apart.

It does nothing until the Roku is pointed at it. In the
[Stitch](https://github.com/jeremy-albinet/Stitch-Revitalized-For-Roku) channel,
go to **Settings -> Proxy URL** and enter the server's address on the LAN:

```
http://<server-ip>:8080
```

Leave that field empty to disable the proxy; regular Twitch streams are
unaffected either way.

## Remote access with WireGuard

The `wireguard` role runs a VPN on UDP 443. A connected device can reach every
port on the server and on studio (the Mac at `studio_ip`, as
`studio.<parent_domain>`), and nothing else: not the rest of the LAN, and not
the internet. It's a split tunnel, so other traffic stays on the local network,
while DNS goes to the server's dnsmasq so local names resolve.

One-time manual steps:

1. On the router, forward **UDP** 443 to the server. (TCP 443 stays pointed at
   nginx; the two don't conflict.)
2. Once SSH over the VPN works, delete the router's SSH port forward.

Each device in `wireguard_peers` (`group_vars/home/vars.yml`) needs a private
key under `wireguard_peer_private_keys` in the vault, plus
`wireguard_server_private_key` for the server. Generate keys with `wg genkey`
(`brew install wireguard-tools`).

The playbook writes each device's config, private key included, to the
gitignored `wireguard_clients/` directory. To import one:

* Phone or tablet: in the WireGuard app, add a tunnel from a QR code, and scan
  the output of `qrencode -t ansiutf8 < wireguard_clients/phone.conf`
* Laptop: in the WireGuard app, import `wireguard_clients/laptop.conf`

To revoke a device, remove it from `wireguard_peers` and its key from the
vault, then rerun with `--tags wireguard`.

To use T3 Code remotely, connect the VPN, run `npx t3 pair` on studio, and pair
the app with `http://studio.<parent_domain>:3773`.
