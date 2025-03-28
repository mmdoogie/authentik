---
title: Applications
---

Applications in authentik are the counterpart of providers. They exist in a 1-to-1 relationship, each application needs a provider and every provider can be used with one application.

Applications are used to configure and separate the authorization / access control and the appearance in the Library page.

## Authorization

Application access can be configured using (Policy) Bindings. You can use this to grant access to one or multiple users/groups, or dynamically give access using policies.

By default, all users can access applications when no policies are bound.

When multiple policies/groups/users are attached, you can configure the *Policy engine mode* to either

    - Require users to pass all bindings/be member of all groups (ALL), or
    - Require users to pass either binding/be member of either group (ANY)

## Appearance

The following aspects can be configured:

    - *Name*: This is the name shown for the application card
    - *Launch URL*: The URL that is opened when a user clicks on the application. When left empty, authentik tries to guess it based on the provider
    - *Icon (URL)*: Optionally configure an Icon for the application
    - *Publisher*: Text shown below the application
    - *Description*: Subtext shown on the application card below the publisher

Applications are shown to users when

    - The user has access defined via policies (or the application has no policies bound)
    - A Valid Launch URL is configured/could be guessed, this consists of URLs starting with http:// and https://


#### Hiding applications

To hide applications without modifying policy settings and without removing it, you can simply set the *Launch URL* to `blank://blank`, which will hide the application from users.

Keep in mind, the users still have access, so they can still authorize access when the login process is started from the application.
