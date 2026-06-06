
# Reverse Proxy Configuration

{{ version_badge("add", "0.6.7") }}

When hosting Trailarr behind a reverse proxy (like Nginx, Apache, Caddy, Traefik, etc.), certain configurations are necessary to ensure that the application functions correctly. This includes proper routing of requests and handling of headers.

There are two common scenarios for reverse proxy setups:

1. `https://trailarr.mydomain.com/` (Sub-domain)
2. `https://mydomain.com/trailarr/` (Sub-directory)

## Sub-domain Reverse Proxy Configuration

When hosting the application behind a reverse proxy in a sub-domain (e.g., `https://trailarr.mydomain.com/`), the following configurations can be used as examples.

These are example configurations for common reverse proxies, adjust them as needed for your specific setup.

!!! success ""
    No special configuration is needed in Trailarr for sub-domain setups, but ensure that your reverse proxy forwards the necessary headers.


## Sub-directory Reverse Proxy Configuration

When hosting the application behind a reverse proxy in a sub-directory (e.g., `https://mydomain.com/trailarr/`), additional configuration is required to ensure proper routing and resource loading.

### URL Base Setting

- Make sure to set the `URL Base` in the General Settings of the application to match the sub-directory path used in the reverse proxy. For example, if your application is accessible at `https://mydomain.com/trailarr/`, set the `URL Base` to `/trailarr`.


## Example Configurations

!!! warning
    Remember to replace these with actual values:

      - `http://192.168.1.231:7889` -> Trailarr internal IP and port
      - `trailarr.mydomain.com` -> Your Sub-Domain
      - `/trailarr/` -> Your Sub-Directory path -> set the same for `URL Base` setting in Trailarr

!!! info "Recommended headers"
    The following headers preserve information about the original request that would otherwise be lost when the proxy forwards it:

    | Header | Purpose |
    |---|---|
    | `X-Forwarded-For` | Original client IP address — added automatically by most proxies |
    | `X-Forwarded-Proto` | Original protocol (`http` or `https`) |
    | `X-Forwarded-Host` | Original host name (`mysuperapp.com`) |
    | `X-Forwarded-Prefix` | Sub-directory prefix (`/trailarr`) — required for correct frontend routing in sub-directory setups |

### Nginx

=== "Sub-Domain"
    ```nginx
    server {
        server_name trailarr.mydomain.com;

        location / {
            proxy_pass http://192.168.1.231:7889;

            proxy_set_header Host                $host;
            proxy_set_header X-Real-IP           $remote_addr;
            proxy_set_header X-Forwarded-For     $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto   $scheme;
            proxy_set_header X-Forwarded-Host    $host;

        }
    }
    ```

=== "Sub-Directory"
    ```nginx
    server {
        server_name mydomain.com;

        location /trailarr/ {
            proxy_pass http://192.168.1.231:7889;

            proxy_set_header Host                $host;
            proxy_set_header X-Real-IP           $remote_addr;
            proxy_set_header X-Forwarded-For     $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto   $scheme;
            proxy_set_header X-Forwarded-Host    $host;
            proxy_set_header X-Forwarded-Prefix  /trailarr;
        }
    }
    ```


### Apache

=== "Sub-Domain"
    ```apache
    <VirtualHost *:80>
        ServerName trailarr.mydomain.com
        ProxyPreserveHost On
        ProxyPass "/" "http://192.168.1.231:7889/"
        ProxyPassReverse "/" "http://192.168.1.231:7889/"
        RequestHeader set X-Forwarded-Proto "%{REQUEST_SCHEME}s"
        RequestHeader set X-Forwarded-Host "%{HTTP_HOST}s"
    </VirtualHost>
    ```

=== "Sub-Directory"
    ```apache
    <VirtualHost *:80>
        ServerName mydomain.com
        ProxyPreserveHost On
        ProxyPass "/trailarr/" "http://192.168.1.231:7889/"
        ProxyPassReverse "/trailarr/" "http://192.168.1.231:7889/"
        RequestHeader set X-Forwarded-Proto "%{REQUEST_SCHEME}s"
        RequestHeader set X-Forwarded-Host "%{HTTP_HOST}s"
        RequestHeader set X-Forwarded-Prefix "/trailarr"
    </VirtualHost>
    ```


### Caddy

=== "Sub-Domain"
    ```caddy
    trailarr.mydomain.com {
        reverse_proxy http://192.168.1.231:7889 {
            header_up X-Forwarded-Host {host}
        }
    }
    ```

=== "Sub-Directory"
    ```caddy
    reverse_proxy /trailarr/* http://192.168.1.231:7889 {
        header_up X-Forwarded-Host   {host}
        header_up X-Forwarded-Prefix /trailarr
    }
    ```


### Traefik

=== "Sub-Domain"
    ```yaml
    http:
      routers:
        trailarr:
          rule: "Host(`trailarr.mydomain.com`)"
          service: trailarr-service
      services:
        trailarr-service:
          loadBalancer:
            servers:
              - url: "http://192.168.1.231:7889" 
    ```

=== "Sub-Directory"
    ```yaml
    http:
      routers:
        trailarr:
          rule: "PathPrefix(`/trailarr`)"
          service: trailarr-service
          middlewares:
            - strip-trailarr
            - trailarr-headers
      services:
        trailarr-service:
          loadBalancer:
            servers:
              - url: "http://192.168.1.231:7889"
      middlewares:
        strip-trailarr:
          stripPrefix:
            prefixes:
              - "/trailarr"
        trailarr-headers:
          headers:
            customRequestHeaders:
              X-Forwarded-Prefix: "/trailarr"
    ```


## Additional Notes

- Forward the `X-Forwarded-Prefix` header from reverse proxy to Trailarr. _Recommended — ensures the correct frontend is served when accessed through the proxy._
- Restart Trailarr and reverse proxy to apply the new configuration.
- After setting `URL Base` and restarting, Trailarr is accessible at **both** the local URL (`http://your-ip:7889/`) and the sub-directory URL (`https://mydomain.com/trailarr/`).
- You may need to clear your browser cache or perform a hard refresh to load the resources correctly.

    !!! tip
        `Ctrl + Shift + I` to open Developer Tools -> right-click the `Refresh` button -> select `Empty Cache and Hard Reload`

- If you encounter any issues, and want to revert back to root-only access, find the `.env` file in `config/` folder and remove the value set for `URL_BASE`, then restart the application.


!!! success
    If you are using a different reverse proxy, and successfully configured it to work with Trailarr in a sub-directory, please consider sharing your configuration by opening a new issue or a pull request on our [GitHub repository](https://github.com/nandyalu/trailarr/){:target="_blank"} and we will update the documentation accordingly.

## How It Works

When `URL Base` is set and Trailarr restarts, it does the following:

- Keeps the root `index.html` with `<base href="/">` so the app remains accessible at the local IP and port (`http://your-ip:7889/`).
- Creates a `/{url_base}/` subfolder inside the frontend build directory containing a separate `index.html` patched with `<base href="/{url_base}/">`. This makes the app also accessible at `http://your-ip:7889/{url_base}/` and via the reverse proxy sub-directory URL.
- Registers a middleware that strips the `/{url_base}` prefix from API, WebSocket, and other server-side requests arriving without a reverse proxy (i.e., direct local access at `http://your-ip:7889/{url_base}/api/...`), so they are routed correctly without any proxy stripping needed.
- Reads the `X-Forwarded-Prefix` header (sent by the reverse proxy) to decide which `index.html` to serve when the proxy strips the prefix before forwarding — ensuring Angular loads with the correct base path.

Both access methods work simultaneously after a single restart — no trade-off between local and proxied access.


## Bypassing Authentication via Reverse Proxy

If your reverse proxy already handles authentication (e.g. SSO, OAuth, basic auth at the proxy level) and you want Trailarr to skip its own login screen, configure the proxy to inject the `X-API-KEY` header with your Trailarr API key on every forwarded request. Trailarr will accept the key, issue a session automatically, and the login page will not be shown.

!!! info "Finding your API key"
    Your API key is shown in **Settings → General → API Key**.

!!! warning "Security note"
    Anyone who can send an `X-API-KEY` header directly to Trailarr will bypass authentication. Make sure Trailarr's port is **not** accessible from outside your network — only the reverse proxy should be able to reach it.

Add the following to your existing reverse proxy configuration (in addition to any other headers already set):

=== "Nginx"
    ```nginx
    proxy_set_header X-API-KEY "your-api-key-here";
    ```

=== "Apache"
    ```apache
    RequestHeader set X-API-KEY "your-api-key-here"
    ```

=== "Caddy"
    ```caddy
    header_up X-API-KEY "your-api-key-here"
    ```

=== "Traefik"
    ```yaml
    middlewares:
      trailarr-headers:
        headers:
          customRequestHeaders:
            X-API-KEY: "your-api-key-here"
    ```