# Authentication

This document describes how authentication works in the application.

## Login Flow

The authentication process is handled by the core auth logic:

[grip:auth-logic]

Users provide their username and password, which are verified against stored credentials.

## Session Management

After successful authentication, a session is created:

[grip:session-create]

Sessions include a secure token and expiration time.
