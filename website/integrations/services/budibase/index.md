---
title: Budibase
---

## What is Budibase

From https://github.com/Budibase/budibase

:::note
Budibase is an open source low-code platform, and the easiest way to build internal tools that improve productivity. 
:::

## Preparation

The following placeholders will be used:

- `budibase.company` is the FQDN of the Budibase install.
- `authentik.company` is the FQDN of the authentik install.

Create an application in authentik. Create an OAuth2/OpenID provider with the following parameters:

- Client Type: `Confidential`
- JWT Algorithm: `RS256`
- Scopes: OpenID, Email and Profile
- RSA Key: Select any available key
- Redirect URIs: `https://budibase.company/api/global/auth/oidc/callback`

Note the Client ID and Client Secret values. Create an application, using the provider you've created above.

## Budibase

In Budibase under `Auth` set the following values

- Config URL: `https://authentik.company/application/o/<Slug of the application from above>/.well-known/openid-configuration`
- Client ID: `Client ID from above`
- Client Secret: `Client Secret from above`