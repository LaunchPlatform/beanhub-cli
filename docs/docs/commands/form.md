# BeanHub Forms

BeanHub Forms lets you define your custom forms and simplify repetitive input tasks.
It also makes it much easier for non-technical users to help you maintain the Beancount books without knowing the syntax.
It's also an open-source library. You must define your custom forms at `.beanhub/forms.yaml` in your Beancount repository.
You can visit [beanhub-forms](https://github.com/LaunchPlatform/beanhub-forms) to learn more about the custom form scheme.

### Serve web app

To make it much easier for BeanHub users to test their BeanHub Forms locally, we added a simple local web app for that in beanhub-cli.
You can run it by

```bash
bh form server
```

It should open the BeanHub Forms web page locally at http://localhost:8080 by default.
It reads the `.beanhub/forms.yaml` file from the current directory and will modify beancount files in the directory, so make sure you cd to your beancount directory before running the command.
To learn more about BeanHub Forms, please read our blog post [Automating Beancount data input with custom forms makes your life 10 times easier!](https://beanhub.io/blog/2023/07/31/automating-beancount-data-input-with-beanhub-custom-forms/).

### List BeanHub Forms

To list BeanHub Forms, simply run

```bash
bh form list
```
### Validate BeanHub Forms doc

To validate BeanHub Forms doc, simply run

```bash
bh form validate
```
