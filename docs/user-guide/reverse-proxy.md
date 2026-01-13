
# Reverse Proxy Configuration

<!-- md:version:add 0.6.7 -->

When hosting Trailarr behind a reverse proxy (like Nginx, Apache, Caddy, Traefik, etc.), certain configurations are necessary to ensure that the application functions correctly. This includes proper routing of requests and handling of headers.

## Subdirectory Reverse Proxy Configuration

When hosting the application behind a reverse proxy in a subdirectory (e.g., `https://example.com/trailarr/`), additional configuration is required to ensure proper routing and resource loading.

### URL Base Setting

- Make sure to set the `URL Base` in the General Settings of the application to match the subdirectory path used in the reverse proxy. For example, if your application is accessible at `https://example.com/trailarr/`, set the `URL Base` to `/trailarr`.

### Reverse Proxy Configuration Examples

#### Nginx

```nginx
location /trailarr/ {
    proxy_pass http://localhost:port/;  # Replace 'port' with the actual port number
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /trailarr;
}
```

#### Apache

```apache
ProxyPass "/trailarr/" "http://localhost:port/"  # Replace 'port' with the actual port number
ProxyPassReverse "/trailarr/" "http://localhost:port/"
RequestHeader set X-Forwarded-Prefix "/trailarr"
```

#### Caddy

```caddy
reverse_proxy /trailarr/* http://localhost:port {  # Replace 'port' with the actual port number
    header_up X-Forwarded-Prefix /trailarr
}
```

#### Traefik

```yaml
http:
  routers:
    trailarr:
      rule: "PathPrefix(`/trailarr`)"
      service: trailarr-service
      middlewares:
        - strip-trailarr
  services:
    trailarr-service:
    loadBalancer:
      servers:
        - url: "http://localhost:port"  # Replace 'port' with the actual port number
  middlewares:
    strip-trailarr:
      stripPrefix:
        prefixes:
          - "/trailarr"
```


### Additional Notes

- Ensure that your reverse proxy is configured to forward the `X-Forwarded-Prefix` header to the application.
- After making these changes, restart Trailarr and your reverse proxy server to apply the new configuration.
- Once you add the `URL Base` and restart Trailarr, you will not be able to access the application at the root URL.
- You may need to clear your browser cache or perform a hard refresh to load the resources correctly.
- If you encounter any issues, and want to revert back to root access, find the `.env` file in `config/` folder and remove the value set for `URL_BASE`, then restart the application.


!!! success
    If you are using a different reverse proxy, and successfully configured it to work with Trailarr in a subdirectory, please consider sharing your configuration by opening a new issue or a pull request on our [GitHub repository](https://github.com/nandyalu/trailarr/){:target="_blank"} and we will update the documentation accordingly.

## How It Works

When the `URL Base` is set and restart Trailarr, Trailarr does the following:

- Identifies that a `URL Base` is set.
- Adds a `root-path` option to the FastAPI application, which tells FastAPI to serve all routes under the specified base path.
- Adjusts the `base href` in the HTML templates to ensure that all relative URLs for resources (like CSS, JS, images) are correctly prefixed with the `URL Base`.

This ensures that when the application is accessed via the reverse proxy in a subdirectory, all routes and resources are correctly resolved.