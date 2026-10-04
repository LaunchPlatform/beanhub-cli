# BeanHub Logout

`bh logout` revokes the access token [`bh login`](./login.md) saved for this computer, then removes it from the local config.

```bash
bh logout
```

The token lives in `<your home folder>/.beanhub/config.toml`.
Logout deletes that token from the file.
If the file only held the token, logout deletes the file.
Other settings in the file, such as a default repository, stay in place.

Running logout when you are not logged in prints `Not logged in` and leaves the config file alone.

Logout calls BeanHub and deletes only this token. Other access tokens on the account stay.
If the token is already invalid, logout still removes it from this computer.
If BeanHub cannot be reached, or the revoke call fails, logout leaves you logged in so you can try again.
An older BeanHub server has no revoke route. Logout still removes the token from this computer and tells you to delete it on the [BeanHub Access Token management page](https://app.beanhub.io/access-tokens/).
