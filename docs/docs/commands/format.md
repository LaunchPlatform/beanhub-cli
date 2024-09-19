# Format beancount files

You can run [beancount-black](https://github.com/LaunchPlatform/beancount-black) formatter against given files by the following command

```bash
bh format main.bean
```

Without the file arguments, the format command will try to format `main.bean` in the current folder, and it will recursively follow all the `include` statements to format all the bean files.
Like this:

```bash
bh format
```
