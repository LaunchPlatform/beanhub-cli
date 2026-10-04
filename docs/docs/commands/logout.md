# BeanHub Logout

`bh logout` removes the BeanHub access token saved on this computer by [`bh login`](./login.md).

```bash
bh logout
```

The token lives in `<your home folder>/.beanhub/config.toml`.
Logout deletes that token.
If the file only held the token, logout deletes the file.
Other settings in the file, such as a default repository, stay in place.

Running logout when you are not logged in prints `Not logged in` and leaves the config file alone.

Logout does not delete the token on BeanHub.
Git and the API keep accepting it until you delete it on the [BeanHub Access Token management page](https://app.beanhub.io/access-tokens/).
